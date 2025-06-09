from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os

from config.database import Config

app = Flask(__name__)
app.config.from_object(Config) # This will now directly use SQLALCHEMY_DATABASE_URI from Config

# 初始化数据库
db = SQLAlchemy(app)

# 示例数据模型
class TestData(db.Model):
    __tablename__ = 'test_data'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@app.route('/')
def home():
    return 'Welcome to the Flask Web Service'

@app.route('/api/data', methods=['GET'])
def get_all_data():
    """获取所有测试数据"""
    try:
        data = TestData.query.all()
        return jsonify([item.to_dict() for item in data])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data', methods=['POST'])
def create_data():
    """创建新的测试数据"""
    try:
        json_data = request.get_json()
        new_data = TestData(
            name=json_data.get('name'),
            value=json_data.get('value')
        )
        db.session.add(new_data)
        db.session.commit()
        return jsonify(new_data.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/<int:data_id>', methods=['GET'])
def get_data(data_id):
    """获取特定ID的测试数据"""
    try:
        data = TestData.query.get_or_404(data_id)
        return jsonify(data.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/<int:data_id>', methods=['PUT'])
def update_data(data_id):
    """更新测试数据"""
    try:
        data = TestData.query.get_or_404(data_id)
        json_data = request.get_json()
        
        data.name = json_data.get('name', data.name)
        data.value = json_data.get('value', data.value)
        
        db.session.commit()
        return jsonify(data.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/<int:data_id>', methods=['DELETE'])
def delete_data(data_id):
    """删除测试数据"""
    try:
        data = TestData.query.get_or_404(data_id)
        db.session.delete(data)
        db.session.commit()
        return jsonify({'message': 'Data deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 创建数据库表
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)