# Type "python -m pytest testing/test_app.py -v" to run the testing, you need to be outside of the testing directory where "app.py" is located.
import pytest
from app import app, db, User
from unittest.mock import patch
import json

# Pytest fixture to configure the app for testing. Sets up SQLite database and returns a test client.
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test_secret_key"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

# Helper function to create and log in a test user.
def login_user(client):
    client.post('/signup', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    client.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)

# Testing home page route.
def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Dublin Bikes" in response.data

# Testing user signup.
def test_signup(client):
    response = client.post('/signup', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Login" in response.data or b"Dublin Bikes" in response.data

    # Confirming that user is created in the database.
    user = User.query.filter_by(username='testuser').first()
    assert user is not None

# Testing logging in and out.
def test_login_logout(client):
    client.post('/signup', data={'username': 'loginuser', 'password': 'testpass'}, follow_redirects=True)
    response = client.post('/login', data={'username': 'loginuser', 'password': 'testpass'}, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Dublin Bikes" in response.data

    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Dublin Bikes" in response.data

# Testing the contact form email submission.
@patch('smtplib.SMTP_SSL')
def test_contact_form(mock_smtp, client):
    login_user(client)
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.post('/submit_contact', data={
        'first': 'Jane',
        'last': 'Doe',
        'email': 'jane@example.com',
        'message': 'Hello!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Dublin Bikes" in response.data or b"Review" in response.data

# Testing stations API with bike station data.
@patch('app.fetch_live_bike_data_dublin')
def test_stations_api(mock_fetch_data, client):
    login_user(client)
    mock_fetch_data.return_value = [
        {"name": "Station A", "number": 101},
        {"name": "Station B", "number": 102}
    ]
    response = client.get('/stations')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]["name"] == "Station A"

# Testing the predict API with all dependencies.
@patch('app.fetch_live_bike_data_dublin')
@patch('app.get_weather_forecast_dublin')
@patch('app.load_station_model')
def test_predict_api(mock_model, mock_weather, mock_bike_data, client):
    login_user(client)

    mock_model.return_value.predict.return_value = [5]
    mock_weather.return_value = {"temperature": 15, "humidity": 80}
    mock_bike_data.return_value = [{"number": 101, "available_bike_stands": 10}]

    response = client.get('/predict?station_id=101&date=2025-04-14&time=12:00:00')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "predicted_available_bikes" in data
    assert isinstance(data["predicted_available_bikes"], int)

# Testing that protected pages are accessible after login.
def test_protected_routes(client):
    login_user(client)
    for route in ['/map', '/weather', '/review']:
        response = client.get(route)
        assert response.status_code == 200

# Testing login failure for invalid credentials.
def test_login_failure(client):
    response = client.post('/login', data={'username': 'baduser', 'password': 'wrong'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Dublin Bikes" in response.data

# Testing to ensure duplicate usernames can't sign up twice.
def test_duplicate_signup(client):
    client.post('/signup', data={'username': 'dupe', 'password': '123'}, follow_redirects=True)
    response = client.post('/signup', data={'username': 'dupe', 'password': '456'}, follow_redirects=True)
    assert response.status_code == 200
    users = User.query.filter_by(username='dupe').all()
    assert len(users) == 1