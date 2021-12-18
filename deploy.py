from forecast_app import create_app
from forecast_app.config import DevelopmentConfig

if __name__ == "__main__":
    app = create_app(DevelopmentConfig)
    app.run(debug=True, host="0.0.0.0", port=5000)
