# Unit testing below. To run type "python -m pytest testing/unit_tests.py -v", you need to be in the same directory as "app.py".
import pytest
from app import (
    get_historical_average_docks,
    get_station_available_docks,
    predict_bike_availability,
    fetch_live_bike_data_dublin,
    get_weather_forecast_dublin,
    load_station_model
)
from unittest.mock import patch, MagicMock
import pandas as pd
import os

# Fixture to mock avg_usage_df used in get_historical_average_docks.
@pytest.fixture(autouse=True)
def patch_avg_usage(monkeypatch):
    test_df = pd.DataFrame({
        'station_id': [1, 1],
        'day_name': [0, 1],
        'hour': [8, 9],
        'avg_docks': [5, 10]
    })
    monkeypatch.setattr("app.avg_usage_df", test_df)

# Testing that the function returns correct dock count when matching entry is found.
def test_get_historical_average_docks_hit():
    assert get_historical_average_docks(1, 0, 8) == 5

# Testing that the function returns 0 when no match is found in historical usage data.
def test_get_historical_average_docks_miss():
    assert get_historical_average_docks(99, 6, 20) == 0

# Testing that the function returns the correct dock count when the station is found.
def test_get_station_available_docks_found():
    data = [{'number': 123, 'available_bike_stands': 7}]
    assert get_station_available_docks(123, data) == 7

# Testing that the, function returns 0 when station ID is not found in bike data.
def test_get_station_available_docks_not_found():
    data = [{'number': 456, 'available_bike_stands': 3}]
    assert get_station_available_docks(123, data) == 0

# Testing that the live bike data fetch succeeds and returns parsed JSON when API is available.
@patch("app.requests.get")
def test_fetch_live_bike_data_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"number": 123, "available_bike_stands": 5}]
    mock_get.return_value = mock_response

    data = fetch_live_bike_data_dublin()
    assert isinstance(data, list)
    assert data[0]["number"] == 123

# Testing that the function raises exception if API returns a failure status.
@patch("app.requests.get")
def test_fetch_live_bike_data_fail(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_get.return_value = mock_response

    with pytest.raises(Exception):
        fetch_live_bike_data_dublin()

# Testing that the weather forecast function correctly parses temperature and humidity from mocked API data.
@patch("app.requests.get")
def test_get_weather_forecast_dublin(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "list": [{
            "dt": 1713070800,
            "main": {"temp": 12.5, "humidity": 82}
        }]
    }
    mock_get.return_value = mock_response
    result = get_weather_forecast_dublin("2025-04-14")
    assert "temperature" in result
    assert "humidity" in result

# Testing the predict availability using mocks for model, weather, and live bike data.
@patch("app.load_station_model")
@patch("app.get_weather_forecast_dublin")
@patch("app.fetch_live_bike_data_dublin")
def test_predict_bike_availability(mock_fetch, mock_weather, mock_model):
    mock_model.return_value.predict.return_value = [4]
    mock_weather.return_value = {"temperature": 15, "humidity": 80}
    mock_fetch.return_value = [{"number": 1, "available_bike_stands": 5}]
    prediction = predict_bike_availability(1, "2025-04-14", "12:00:00")
    assert isinstance(prediction, int)
    assert prediction == 4

# Testing that the function raises FileNotFoundError if the model file path does not exist.
@patch("app.os.path.exists", return_value=False)
def test_load_station_model_file_not_found(mock_exists):
    with pytest.raises(FileNotFoundError):
        load_station_model(999)

# Testing that the weather forecast raises error if API returns no list data.
@patch("app.requests.get")
def test_weather_forecast_no_data(mock_get):
    mock_get.return_value.json.return_value = {"list": []}
    with pytest.raises(ValueError):
        get_weather_forecast_dublin("2025-04-14")

# Testing that prediction works with HH:MM time format input.
@patch("app.load_station_model")
@patch("app.get_weather_forecast_dublin")
@patch("app.fetch_live_bike_data_dublin")
def test_predict_bike_availability_time_format(mock_fetch, mock_weather, mock_model):
    mock_model.return_value.predict.return_value = [3]
    mock_weather.return_value = {"temperature": 16, "humidity": 65}
    mock_fetch.return_value = [{"number": 1, "available_bike_stands": 4}]
    prediction = predict_bike_availability(1, "2025-04-14", "12:00")
    assert isinstance(prediction, int)
    assert prediction == 3

# Testing that historical data path is used in prediction logic when prediction time is in the distant future.
@patch("app.load_station_model")
@patch("app.get_weather_forecast_dublin")
def test_predict_uses_historical_data(mock_weather, mock_model):
    mock_model.return_value.predict.return_value = [7]
    mock_weather.return_value = {"temperature": 18, "humidity": 60}
    prediction = predict_bike_availability(1, "2030-01-01", "12:00:00")
    assert isinstance(prediction, int)
    assert prediction == 7