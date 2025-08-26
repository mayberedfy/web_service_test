# from app import app, db

# def init_database():
#     """初始化数据库"""
#     with app.app_context():
#         # 创建所有表
#         db.create_all()
#         print("数据库表创建成功！")

# if __name__ == '__main__':
#     init_database()


#!/usr/bin/env python3
"""初始化数据库数据"""
from src.app import app
from src.extensions import db
from src.models.admin_user_model import User
from src.models.admin_api_keys import ApiKey

def create_admin_user():
    """创建默认管理员用户"""
    with app.app_context():
        # 检查是否已存在管理员
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                permissions=['*'],  # 所有权限
                is_active=True,
                is_verified=True
            )
            admin.set_password('admin123')  # 生产环境请修改
            
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created: admin/admin123")
        else:
            print("Admin user already exists")

def create_default_api_keys():
    """创建默认API密钥"""
    with app.app_context():
        # 为APP上传创建API密钥
        if not ApiKey.query.filter_by(key_name='Default Upload Key').first():
            api_key, raw_key = ApiKey.generate_key(
                name='Default Upload Key',
                scope='upload',
                permissions=['upload', 'write']
            )
            
            db.session.add(api_key)
            db.session.commit()
            print(f"Upload API key created: {raw_key}")
            print("Please save this key securely!")

if __name__ == '__main__':
    create_admin_user()
    create_default_api_keys()