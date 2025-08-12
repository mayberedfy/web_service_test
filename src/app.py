from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from src.config.database import Config
from src.extensions import db
from src.routes import wifi_board_tests_bp, driver_board_tests_bp, integrate_tests_bp, wifi_test_logs_bp,temperature_data_bp
app = Flask(__name__)
app.config.from_object(Config)

# 开启 CORS 支持，允许前端 http://localhost:5173 访问
CORS(app, origins=["http://localhost:5173"])

db.init_app(app)

app.register_blueprint(wifi_board_tests_bp) 
app.register_blueprint(driver_board_tests_bp)
app.register_blueprint(integrate_tests_bp) 
app.register_blueprint(wifi_test_logs_bp)
app.register_blueprint(temperature_data_bp)


migrate = Migrate(app, db)

@app.route('/')
def home():
    return 'Welcome to the Flask Web Service'

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Ensure all tables are created
    app.run(debug=True, host='127.0.0.1', port=5000)