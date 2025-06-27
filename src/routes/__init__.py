from flask import Blueprint

# Create a blueprint for the routes
routes_bp = Blueprint('routes', __name__)

# Import route handlers
from .wifi_board_test_routes import wifi_board_tests_bp
from .driver_board_test_routes import driver_board_tests_bp
from .integrate_test_routes import integrate_tests_bp

__all__ = [
    'routes_bp',
    'wifi_board_tests_bp',
    'driver_board_tests_bp', 
    'integrate_tests_bp'
]