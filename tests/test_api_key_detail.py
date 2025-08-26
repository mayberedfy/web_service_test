#!/usr/bin/env python3
"""测试 API Key 详情接口"""

import requests
import json

# 配置
API_BASE_URL = "http://localhost:5000/api"
USERNAME = "admin"
PASSWORD = "admin123"

def test_api_key_detail():
    """测试API Key详情功能"""
    
    # 1. 登录获取token
    print("1. 登录获取访问令牌...")
    login_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.json()}")
        return
    
    token_data = login_response.json()
    access_token = token_data.get('access_token')
    headers = {'Authorization': f'Bearer {access_token}'}
    print("✓ 登录成功")
    
    # 2. 创建测试API Key
    print("\n2. 创建测试API Key...")
    create_response = requests.post(f"{API_BASE_URL}/api-keys", 
        headers=headers,
        json={
            "key_name": "详情测试密钥",
            "key_description": "这是用于测试获取详情功能的API密钥",
            "scope": "upload",
            "permissions": ["upload", "read", "write"]
        })
    
    if create_response.status_code != 201:
        print(f"❌ 创建API Key失败: {create_response.json()}")
        return
    
    create_data = create_response.json()
    api_key_id = create_data['api_key']['id']
    print(f"✓ API Key创建成功，ID: {api_key_id}")
    
    # 3. 获取API Key详情
    print("\n3. 获取API Key详情...")
    detail_response = requests.get(f"{API_BASE_URL}/api-keys/{api_key_id}", 
        headers=headers)
    
    if detail_response.status_code == 200:
        detail_data = detail_response.json()
        api_key_detail = detail_data['api_key']
        
        print("✓ 成功获取API Key详情:")
        print(f"  ID: {api_key_detail['id']}")
        print(f"  名称: {api_key_detail['key_name']}")
        print(f"  描述: {api_key_detail['key_description']}")
        print(f"  作用域: {api_key_detail['scope']}")
        print(f"  权限: {api_key_detail['permissions']}")
        print(f"  状态: {api_key_detail.get('status', 'unknown')}")
        print(f"  是否激活: {api_key_detail['is_active']}")
        print(f"  使用次数: {api_key_detail['usage_count']}")
        print(f"  创建时间: {api_key_detail['create_time']}")
        print(f"  最后使用: {api_key_detail.get('last_used', '从未使用')}")
        
        # 创建者信息
        if 'creator_info' in api_key_detail:
            creator = api_key_detail['creator_info']
            print(f"  创建者: {creator['username']} ({creator['role']})")
        
        print(f"\n📊 详细信息包含的字段:")
        for key in sorted(api_key_detail.keys()):
            print(f"    - {key}")
            
    else:
        print(f"❌ 获取API Key详情失败: {detail_response.json()}")
        return
    
    # 4. 测试获取不存在的API Key
    print("\n4. 测试获取不存在的API Key...")
    not_found_response = requests.get(f"{API_BASE_URL}/api-keys/non-existent-id", 
        headers=headers)
    
    if not_found_response.status_code == 404:
        print("✓ 正确返回404错误")
    else:
        print(f"❌ 未正确处理不存在的ID: {not_found_response.status_code}")
    
    # 5. 清理测试数据
    print("\n5. 清理测试数据...")
    delete_response = requests.delete(f"{API_BASE_URL}/api-keys/{api_key_id}", 
        headers=headers)
    
    if delete_response.status_code == 200:
        print("✓ 测试数据清理完成")
    else:
        print(f"⚠️ 清理测试数据失败，请手动删除: {delete_response.json()}")
    
    print("\n🎉 API Key详情接口测试完成！")

if __name__ == "__main__":
    try:
        test_api_key_detail()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
