import os
from dotenv import load_dotenv

load_dotenv()
#root   rootcome
class Config:
    # MySQL数据库配置
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:"
        f"{os.getenv('DB_PASSWORD', 'root')}@"
        f"{os.getenv('DB_HOST', '121.4.54.191')}:"
        f"{os.getenv('DB_PORT', '3306')}/"
        f"{os.getenv('DB_NAME', 'my_db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')