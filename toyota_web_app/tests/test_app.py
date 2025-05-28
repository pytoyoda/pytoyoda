# toyota_web_app/tests/test_app.py
import pytest
from flask import session, url_for
from unittest.mock import patch, MagicMock
# asyncio import might not be strictly needed if all async methods are mocked to return direct results
# However, pytest.mark.asyncio might still require it for test function discovery.
import asyncio

# Synchronous mock for app.run_async
def sync_run_async_mock(arg_to_return):
    # This mock assumes the 'arg_to_return' is the actual result
    # that the awaited coroutine (which was passed to the real run_async) would produce.
    # In this new strategy, 'arg_to_return' will be the direct output from the mocked pytoyoda methods.
    return arg_to_return

def test_login_page_loads(client):
    response = client.get(url_for('login'))
    assert response.status_code == 200
    assert b"Toyota Connected Services Login" in response.data

# No longer needs @pytest.mark.asyncio if all operations become synchronous due to mocking
def test_login_success_redirects_to_dashboard(client):
    with patch('toyota_web_app.app.MyT') as mock_myt_constructor:
        mock_client_instance = MagicMock()

        # Mock pytoyoda async methods to return direct data
        mock_client_instance.login = MagicMock(return_value=None) # login() returns None

        mock_vehicle = MagicMock()
        mock_vehicle.vin = "TESTVINLOGIN"
        mock_vehicle.nickname = "Login Test Car"
        mock_client_instance.get_vehicles = MagicMock(return_value=[mock_vehicle]) # get_vehicles() returns a list

        mock_myt_constructor.return_value = mock_client_instance

        with patch('toyota_web_app.app.run_async', side_effect=sync_run_async_mock) as mock_run_async_func:
            response = client.post(url_for('login'), data={
                'username': 'testuser',
                'password': 'testpassword'
            }, follow_redirects=True)

            assert response.status_code == 200
            assert b"Welcome, testuser!" in response.data
            assert b"Your Vehicles:" in response.data

            mock_client_instance.login.assert_called_once()
            mock_client_instance.get_vehicles.assert_called_once()
            # Assert that run_async was called with the results of the direct calls
            mock_run_async_func.assert_any_call(None) # Result of client.login()
            mock_run_async_func.assert_any_call([mock_vehicle]) # Result of client.get_vehicles()


def test_dashboard_requires_login(client):
    response = client.get(url_for('dashboard'), follow_redirects=True)
    assert response.status_code == 200
    assert b"Toyota Connected Services Login" in response.data

# No longer needs @pytest.mark.asyncio
def test_logout(client):
    # First, log in to establish a session
    with patch('toyota_web_app.app.MyT') as mock_myt_constructor:
        mock_client_instance = MagicMock()
        mock_client_instance.login = MagicMock(return_value=None)
        mock_client_instance.get_vehicles = MagicMock(return_value=[]) # Simulating dashboard load during login

        mock_myt_constructor.return_value = mock_client_instance

        with patch('toyota_web_app.app.run_async', side_effect=sync_run_async_mock):
            # Simulate a login post request to populate session
            client.post(url_for('login'), data={'username': 'testuser', 'password': 'testpassword'})

    # Now test logout
    response = client.get(url_for('logout'), follow_redirects=True)
    assert response.status_code == 200
    assert b"Toyota Connected Services Login" in response.data
    with client.session_transaction() as sess:
        assert 'username' not in sess
        assert 'logged_in' not in sess

# No longer needs @pytest.mark.asyncio
def test_vehicle_details_page_loads_with_mock_data(client):
    mock_vehicle_vin = "TESTVIN123"

    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'testuser'
        sess['password'] = 'testpassword'
        sess['vehicles'] = [{'vin': mock_vehicle_vin, 'nickname': 'Test Car'}]

    with patch('toyota_web_app.app.MyT') as mock_myt_constructor:
        mock_vehicle_obj = MagicMock()
        mock_vehicle_obj.vin = mock_vehicle_vin
        mock_vehicle_obj.nickname = "Test Car"

        mock_dashboard_data = {'fuel_level': 50, 'another_key': 'test_value'}
        mock_vehicle_obj.dashboard = MagicMock()
        mock_vehicle_obj.dashboard.model_dump.return_value = mock_dashboard_data

        mock_vehicle_obj.electric_status = None
        mock_vehicle_obj.location = None
        mock_vehicle_obj.lock_status = None
        mock_vehicle_obj.notifications = [] # Assuming this is a direct attribute, not an async method
        mock_vehicle_obj.get_latest_service_history = MagicMock(return_value=None) # Synchronous method
        mock_vehicle_obj.last_trip = None # Assuming direct attribute

        # Mock async methods to return direct data
        mock_vehicle_obj.update = MagicMock(return_value=None)

        mock_summary_data_obj = MagicMock() # This is what get_current_day_summary would return
        mock_summary_data_obj.model_dump.return_value = {'total_trips': 5}
        mock_vehicle_obj.get_current_day_summary = MagicMock(return_value=mock_summary_data_obj)

        mock_client_instance = MagicMock()
        mock_client_instance.login = MagicMock(return_value=None)
        mock_client_instance.get_vehicles = MagicMock(return_value=[mock_vehicle_obj])

        mock_myt_constructor.return_value = mock_client_instance

        with patch('toyota_web_app.app.run_async', side_effect=sync_run_async_mock) as mock_run_async_func:
            response = client.get(url_for('vehicle_details', vin=mock_vehicle_vin))

    assert response.status_code == 200
    assert b"Vehicle Statistics: Test Car" in response.data
    assert b"TESTVIN123" in response.data

    print("DEBUG START: response.data for vehicle_details")
    print(response.data.decode('utf-8'))
    print("DEBUG END: response.data for vehicle_details")

    assert b"Dashboard Information" in response.data
    assert b"fuel_level" in response.data
    assert b"another_key" in response.data # Check for new key
    assert b"Today&#39;s Summary" in response.data # Check for another section
    assert b"total_trips" in response.data # Check for data from summary

    # Assert that run_async was called with the direct results
    mock_run_async_func.assert_any_call(None) # For client.login()
    mock_run_async_func.assert_any_call([mock_vehicle_obj]) # For client.get_vehicles()
    mock_run_async_func.assert_any_call(None) # For vehicle.update()
    mock_run_async_func.assert_any_call(mock_summary_data_obj) # For vehicle.get_current_day_summary()
