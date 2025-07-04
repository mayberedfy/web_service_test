from flask import Flask

from config.database import Config
from src.extensions import db
from src.routes import wifi_board_tests_bp, driver_board_tests_bp, integrate_tests_bp
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(wifi_board_tests_bp) 
app.register_blueprint(driver_board_tests_bp)
app.register_blueprint(integrate_tests_bp) 



@app.route('/')
def home():
    return 'Welcome to the Flask Web Service'

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Ensure all tables are created
    app.run(debug=True, host='0.0.0.0', port=5000, debug=False, use_reloader=False)