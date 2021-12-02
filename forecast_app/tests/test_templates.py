def test_views(client):
    """Test that all pages return 200 and have the expected content"""

    pages = {
        "/": "Login",
        "/load-data": "Load Data",
        "/weather-data": "Weather Data",
        "/forecast": "Forecast",
        "/instructions": "Instructions",
        "/model-settings": "Model Settings",
        "/user-settings": "User Settings",
    }

    for route, page_name in pages.items():
        response = client.get(route)
        assert response.status_code == 200
        assert page_name in str(response.data)
