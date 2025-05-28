# Toyota Car Statistics Web App - Deployment Guide

This guide outlines the steps to deploy the Toyota Car Statistics web application on a Raspberry Pi (or any Linux-based system).

## Prerequisites

1.  **Raspberry Pi Setup:**
    *   A Raspberry Pi with a compatible OS (e.g., Raspberry Pi OS).
    *   Internet connectivity.
    *   Python 3.8+ and pip installed.
    *   Git installed.

2.  **Project Files:**
    *   Clone this repository or transfer the project files to your Raspberry Pi.

## Installation and Setup

1.  **Install Poetry:**
    If Poetry is not already installed, install it:
    ```bash
    pip install poetry
    ```

2.  **Install Project Dependencies:**
    Navigate to the root directory of the project (where `pyproject.toml` is located) and run:
    ```bash
    poetry install --no-dev
    ```
    This will install the application and its dependencies, including Flask and Gunicorn.

3.  **Firewall Configuration (if applicable):**
    If you have a firewall enabled (like `ufw`), allow traffic on the port Gunicorn will use (e.g., 8000):
    ```bash
    sudo ufw allow 8000/tcp
    ```

## Running the Application with Gunicorn

1.  **Navigate to the Web App Directory:**
    Change to the directory containing the Flask app:
    ```bash
    cd /path/to/your/project/toyota_web_app 
    ```
    (Replace `/path/to/your/project/` with the actual path)


2.  **Start Gunicorn:**
    Run the application using Gunicorn. You'll need to point Gunicorn to the Flask application instance. If your Flask app file is `app.py` and the Flask instance is named `app`, the command is:
    ```bash
    poetry run gunicorn --workers 2 --bind 0.0.0.0:8000 app:app
    ```
    *   `--workers 2`: Adjust the number of worker processes based on your Raspberry Pi's capabilities (2-4 is usually a good starting point for a Pi 3/4).
    *   `--bind 0.0.0.0:8000`: This makes the app accessible from other devices on your network on port 8000.
    *   `app:app`: Refers to the `app` object within the `app.py` file.

3.  **Accessing the Application:**
    Open a web browser on a device connected to the same network as your Raspberry Pi and navigate to `http://<RASPBERRY_PI_IP_ADDRESS>:8000`.

## Running as a Service (Optional but Recommended)

For long-term deployment, you should run Gunicorn as a systemd service so it starts automatically on boot and restarts if it crashes.

1.  **Create a systemd service file:**
    Create a file named `toyota-webapp.service` in `/etc/systemd/system/`:
    ```bash
    sudo nano /etc/systemd/system/toyota-webapp.service
    ```
    Paste the following content, adjusting paths and user as necessary:

    ```ini
    [Unit]
    Description=Gunicorn instance to serve Toyota Car Statistics web app
    After=network.target

    [Service]
    User=pi # Replace with your username if different
    Group=www-data # Or your user's group
    WorkingDirectory=/path/to/your/project/toyota_web_app
    ExecStart=/path/to/your/project/.venv/bin/gunicorn --workers 2 --bind 0.0.0.0:8000 app:app
    # Make sure the path to gunicorn in .venv is correct. You can find it with 'poetry env info --path'/bin/gunicorn

    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
    *   **Important:** Replace `/path/to/your/project/` with the actual absolute path to your project directory.
    *   **Important:** Ensure the `User` and `Group` are correct for your setup.
    *   **Important:** The `ExecStart` path to Gunicorn must be the one within the virtual environment created by Poetry. You can get the environment path with `poetry env info --path` and then append `/bin/gunicorn`.

2.  **Reload systemd, enable and start the service:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable toyota-webapp.service
    sudo systemctl start toyota-webapp.service
    ```

3.  **Check status:**
    ```bash
    sudo systemctl status toyota-webapp.service
    ```

## Security Note on Credentials
This application currently stores Toyota Connected Services credentials (username and password) in the Flask session during runtime after login. For a production environment, especially one accessible over a network, this is not ideal. Consider more secure ways to handle credentials if this were a production application for wider use, such as environment variables for initial setup or a dedicated secrets management solution (though that might be overkill for a personal Raspberry Pi project). The current approach relies on the security of your local network and Raspberry Pi.
