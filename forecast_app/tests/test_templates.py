from forecast_app.commands import upload_demo_data


def test_templates(client):
    """Test that all pages return 200 and have the expected content"""

    pages = {
        "/": "Login",
        "/historical-load-data": "Historical Load Data",
        "/forecast-weather-data": "Forecast Weather Data",
        "/historical-weather-data": "Historical Weather Data",
        "/forecast": "Forecast",
        "/instructions": "Instructions",
        "/model-settings": "Model Settings",
        "/user-settings": "User Settings",
    }

    for route, page_name in pages.items():
        response = client.get(route)
        assert response.status_code == 200
        assert page_name in str(response.data)

    # Test again but with data
    upload_demo_data()
    for route, page_name in pages.items():
        response = client.get(route)
        assert response.status_code == 200
        assert page_name in str(response.data)
