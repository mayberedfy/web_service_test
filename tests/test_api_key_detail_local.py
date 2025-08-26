#!/usr/bin/env python3
"""本地测试 API Key 详情功能"""

from src.app import app
from src.extensions import db
from src.models.admin_api_keys import ApiKey
from src.models.admin_user_model import User
from src.routes.admin_api_key_routes import get_api_key_detail
from flask import g
import json

def test_api_key_detail_function():
    """本地测试API Key详情功能"""
    with app.app_context():
        print("测试 API Key 详情功能...")
        
        try:
            # 创建一个测试用户用作 g.current_user
            test_user = User.query.filter_by(username='admin').first()
            if not test_user:
                print("❌ 请确保存在admin用户")
                return
            
            # 设置当前用户到上下文
            g.current_user = test_user
            
            # 1. 创建测试API密钥
            print("1. 创建测试API密钥...")
            api_key, raw_key = ApiKey.generate_key(
                name="详情测试密钥",
                description="这是用于测试详情获取功能的API密钥，包含完整的元数据信息",
                scope="manage",
                permissions=["upload", "read", "write", "delete"],
                created_by=test_user.id
            )
            
            db.session.add(api_key)
            db.session.commit()
            
            print(f"✓ 测试API密钥创建成功")
            print(f"  ID: {api_key.id}")
            print(f"  名称: {api_key.key_name}")
            print(f"  创建者: {test_user.username}")
            
            # 2. 模拟使用密钥（增加使用次数）
            print("\n2. 模拟密钥使用...")
            api_key.update_usage()
            api_key.update_usage()
            api_key.update_usage()
            db.session.commit()
            print(f"✓ 模拟使用3次，当前使用次数: {api_key.usage_count}")
            
            # 3. 直接调用详情方法测试
            print("\n3. 测试获取详情功能...")
            
            # 模拟Flask路由环境
            with app.test_request_context():
                g.current_user = test_user
                response = get_api_key_detail(api_key.id)
                
                if hasattr(response, 'get_json'):
                    detail_data = response.get_json()
                    api_key_detail = detail_data.get('api_key', {})
                    
                    print("✓ 成功获取API密钥详情:")
                    print(f"  基本信息:")
                    print(f"    - ID: {api_key_detail.get('id')}")
                    print(f"    - 名称: {api_key_detail.get('key_name')}")
                    print(f"    - 描述: {api_key_detail.get('key_description')}")
                    print(f"    - 作用域: {api_key_detail.get('scope')}")
                    print(f"    - 状态: {api_key_detail.get('status')}")
                    
                    print(f"  权限信息:")
                    print(f"    - 权限列表: {api_key_detail.get('permissions')}")
                    print(f"    - 权限数量: {api_key_detail.get('permissions_count')}")
                    print(f"    - 有写权限: {api_key_detail.get('has_write_permission')}")
                    print(f"    - 有读权限: {api_key_detail.get('has_read_permission')}")
                    
                    print(f"  使用统计:")
                    print(f"    - 使用次数: {api_key_detail.get('usage_count')}")
                    print(f"    - 使用频率: {api_key_detail.get('usage_frequency')}")
                    print(f"    - 最后使用: {api_key_detail.get('last_used', '从未使用')}")
                    
                    print(f"  时间信息:")
                    print(f"    - 创建时间: {api_key_detail.get('create_time')}")
                    print(f"    - 创建天数: {api_key_detail.get('created_days_ago')}")
                    print(f"    - 是否过期: {api_key_detail.get('is_expired')}")
                    
                    if 'creator_info' in api_key_detail:
                        creator = api_key_detail['creator_info']
                        print(f"  创建者信息:")
                        print(f"    - 用户名: {creator.get('username')}")
                        print(f"    - 角色: {creator.get('role')}")
                    
                    print(f"\n📋 返回的所有字段 ({len(api_key_detail)} 个):")
                    for key in sorted(api_key_detail.keys()):
                        value = api_key_detail[key]
                        print(f"    - {key}: {type(value).__name__}")
                else:
                    print(f"❌ 获取详情失败: {response}")
            
            # 4. 测试不存在的密钥
            print("\n4. 测试获取不存在的密钥...")
            with app.test_request_context():
                g.current_user = test_user
                not_found_response = get_api_key_detail("non-existent-id")
                
                if hasattr(not_found_response, 'status_code'):
                    if not_found_response.status_code == 404:
                        print("✓ 正确返回404错误")
                    else:
                        print(f"❌ 状态码不正确: {not_found_response.status_code}")
            
            # 5. 清理测试数据
            print("\n5. 清理测试数据...")
            db.session.delete(api_key)
            db.session.commit()
            print("✓ 测试数据已清理")
            
            print("\n🎉 API Key详情功能测试完成！")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 尝试清理
            try:
                db.session.rollback()
            except:
                pass

if __name__ == "__main__":
    test_api_key_detail_function()
