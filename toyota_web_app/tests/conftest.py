# toyota_web_app/tests/conftest.py
import pytest
from toyota_web_app.app import app as flask_app

@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key",
        "WTF_CSRF_ENABLED": False, # If you were using Flask-WTF
        "SERVER_NAME": "localhost.test" # Added: Essential for url_for in some test contexts
    })
    # The previously added 'with app.app_context()' was for the client fixture,
    # but setting SERVER_NAME directly in app.config is more robust for url_for.
    yield flask_app

@pytest.fixture
def client(app):
    # Ensure app context is active for the client, good for session management etc.
    with app.app_context():
        yield app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
