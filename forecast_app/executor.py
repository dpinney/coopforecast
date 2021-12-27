from flask_executor import Executor
import atexit

from forecast_app.models import ForecastModel

executor = Executor()


def close_running_threads():
    executor.shutdown(wait=False)


# Ensure that threads shut down on exit
atexit.register(close_running_threads)
