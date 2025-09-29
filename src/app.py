from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import datetime, timezone

# 导入新的认证模块
from src.auth.jwt_config import init_jwt
from src.auth.rate_limiter import init_limiter

from src.config.database import Config
from src.extensions import db

# 导入新的认证路由
from src.routes.admin_auth_routes import auth_bp
from src.routes.admin_user_manage_routes import user_mgmt_bp
from src.routes.admin_api_key_routes import api_key_bp

# 导入现有路由
from src.routes import (
    wifi_board_tests_bp, 
    driver_board_tests_bp, 
    integrate_tests_bp, 
    wifi_test_logs_bp,
    temperature_data_bp
)

app = Flask(__name__)
app.config.from_object(Config)

# 开启 CORS 支持
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://39.174.166.94:5173",
    "https://your-admin-domain.com"
])

# 初始化数据库
db.init_app(app)

# 初始化认证系统
init_jwt(app)
init_limiter(app)

# 注册认证相关路由
app.register_blueprint(auth_bp)
app.register_blueprint(user_mgmt_bp)
app.register_blueprint(api_key_bp)

# 注册业务路由
app.register_blueprint(wifi_board_tests_bp) 
app.register_blueprint(driver_board_tests_bp)
app.register_blueprint(integrate_tests_bp) 
app.register_blueprint(wifi_test_logs_bp)
app.register_blueprint(temperature_data_bp)

migrate = Migrate(app, db)

@app.route('/')
def home():
    return 'Welcome to the Flask Web Service'

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 确保所有表都创建
    app.run(debug=True, host='127.0.0.1', port=5000)