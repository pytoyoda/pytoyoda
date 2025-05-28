from flask import Flask, render_template, request, redirect, url_for, session
import os
import asyncio
from pytoyoda.client import MyT
from pytoyoda.exceptions import ToyotaApiError # Changed from PytoyotaError

app = Flask(__name__)
app.secret_key = os.urandom(24) # For session management

# Helper function to run async code in Flask
def run_async(func):
    return asyncio.run(func)

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        client = MyT(username, password)
        try:
            run_async(client.login())
            session['username'] = username
            session['password'] = password # Storing password in session is not recommended for production
            session['logged_in'] = True 
            return redirect(url_for('dashboard'))
        except ToyotaApiError as e: # Changed from PytoyotaError
            error = f"Login failed: {e}"
        except Exception as e:
            error = f"An unexpected error occurred: {e}"
            
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))

    username = session.get('username')
    password = session.get('password') # Retrieve password (not ideal for production)
    vehicles = None
    error = None

    if not username or not password:
        return redirect(url_for('login'))

    client = MyT(username, password)
    try:
        # Attempt to login, tokens might be reused if still valid by the client
        run_async(client.login()) 
        raw_vehicles = run_async(client.get_vehicles())
        # Convert Vehicle objects to a list of dicts for template rendering
        # or ensure Vehicle objects have necessary attributes directly accessible
        vehicles = []
        if raw_vehicles:
            for v in raw_vehicles:
                vehicles.append({
                    "vin": v.vin,
                    "nickname": v.nickname,
                    # Add other details if needed by the template directly
                })
        session['vehicles'] = vehicles # Store for other routes if needed
    except ToyotaApiError as e: # Changed from PytoyotaError
        error = f"Could not retrieve vehicle data: {e}"
        if "Authentication failed" in str(e) or "TOKEN_INVALID" in str(e): # Crude check
            session.pop('logged_in', None) # Force re-login
            return redirect(url_for('login'))
    except Exception as e:
        error = f"An unexpected error occurred while fetching vehicles: {e}"

    return render_template('dashboard.html', username=username, vehicles=vehicles, error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('password', None)
    session.pop('logged_in', None)
    session.pop('vehicles', None)
    return redirect(url_for('login'))

@app.route('/vehicle/<vin>')
def vehicle_details(vin):
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    # Logic to fetch and display specific vehicle stats will be added here
    # For now, ensure the user is logged in and has access to this VIN
    # You might want to check if the VIN belongs to the user's vehicles stored in session
    
    # Placeholder for fetching vehicle details if needed again or using session data
    # For example, find the vehicle in session['vehicles']
    vehicle_info = None
    username = session.get('username')
    password = session.get('password') # Retrieve password (not ideal for production)
    error = None
    vehicle_stats = {}
    target_vehicle_info = None # To store basic info like VIN and nickname

    if not username or not password:
        return redirect(url_for('login'))

    # Find basic vehicle info (like nickname) from session first
    if 'vehicles' in session:
        for v_info in session['vehicles']:
            if v_info['vin'] == vin:
                target_vehicle_info = v_info
                break
    
    if not target_vehicle_info:
        # If not in session (e.g. direct access or session expired for this part)
        # or if we want to ensure we always use the latest nickname
        # This part might be redundant if dashboard always populates session['vehicles'] correctly
        # For now, we'll proceed assuming target_vehicle_info is mainly for nickname display
        # and the main vehicle object will be fetched below.
        # If target_vehicle_info is still None, we can set a default or try to fetch it.
        target_vehicle_info = {"vin": vin, "nickname": "N/A"} # Basic default

    client = MyT(username, password)
    try:
        run_async(client.login()) # Ensure client is logged in
        vehicles_list = run_async(client.get_vehicles())
        
        found_vehicle_obj = None
        if vehicles_list:
            for v_obj in vehicles_list:
                if v_obj.vin == vin:
                    found_vehicle_obj = v_obj
                    # Update target_vehicle_info with potentially more current nickname
                    target_vehicle_info['nickname'] = v_obj.nickname 
                    break
        
        if found_vehicle_obj:
            run_async(found_vehicle_obj.update()) # Refresh data for the specific vehicle

            vehicle_stats['dashboard_info'] = found_vehicle_obj.dashboard.model_dump() if found_vehicle_obj.dashboard else None
            vehicle_stats['electric_status'] = found_vehicle_obj.electric_status.model_dump() if found_vehicle_obj.electric_status else None
            vehicle_stats['location_info'] = found_vehicle_obj.location.model_dump() if found_vehicle_obj.location else None
            vehicle_stats['lock_status'] = found_vehicle_obj.lock_status.model_dump() if found_vehicle_obj.lock_status else None
            vehicle_stats['notifications'] = [n.model_dump() for n in found_vehicle_obj.notifications] if found_vehicle_obj.notifications else None
            
            # Service history might be None or the method might return None
            latest_service_obj = found_vehicle_obj.get_latest_service_history()
            vehicle_stats['latest_service'] = latest_service_obj.model_dump() if latest_service_obj else None
            
            vehicle_stats['last_trip'] = found_vehicle_obj.last_trip.model_dump() if found_vehicle_obj.last_trip else None
            
            # Daily summary needs an async call
            daily_summary_obj = run_async(found_vehicle_obj.get_current_day_summary())
            vehicle_stats['daily_summary'] = daily_summary_obj.model_dump() if daily_summary_obj else None
            
        else:
            error = "Vehicle not found."

    except ToyotaApiError as e: # Changed from PytoyotaError
        error = f"Could not retrieve vehicle data: {e}"
        if "Authentication failed" in str(e) or "TOKEN_INVALID" in str(e):
            session.pop('logged_in', None)
            return redirect(url_for('login'))
    except Exception as e:
        error = f"An unexpected error occurred: {e}"

    return render_template('vehicle_details.html', 
                           vehicle_info=target_vehicle_info, 
                           stats=vehicle_stats, 
                           error=error,
                           username=username) # Pass username for consistency if needed by layout

if __name__ == '__main__':
    app.run(debug=True)
