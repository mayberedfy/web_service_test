#!/usr/bin/env python3
"""测试 key_description 字段是否正确添加"""

from src.app import app
from src.extensions import db
from src.models.admin_api_keys import ApiKey

def test_key_description_field():
    with app.app_context():
        print("测试 key_description 字段...")
        
        try:
            # 创建一个测试API密钥
            api_key, raw_key = ApiKey.generate_key(
                name="Test Key",
                description="这是一个测试密钥，用于验证新字段功能",
                scope="upload",
                permissions=["upload", "read"]
            )
            
            # 保存到数据库
            db.session.add(api_key)
            db.session.commit()
            
            print(f"✓ 成功创建测试API密钥")
            print(f"  ID: {api_key.id}")
            print(f"  名称: {api_key.key_name}")
            print(f"  描述: {api_key.key_description}")
            print(f"  前缀: {api_key.key_prefix}")
            
            # 转换为字典验证
            api_dict = api_key.to_dict()
            print(f"✓ to_dict() 包含 key_description: {'key_description' in api_dict}")
            print(f"  key_description 值: {api_dict.get('key_description')}")
            
            # 查询验证
            retrieved = ApiKey.query.filter_by(key_name="Test Key").first()
            print(f"✓ 从数据库查询到的描述: {retrieved.key_description}")
            
            # 清理测试数据
            db.session.delete(api_key)
            db.session.commit()
            print("✓ 测试数据已清理")
            
            print("\n🎉 key_description 字段功能测试成功！")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_key_description_field()
