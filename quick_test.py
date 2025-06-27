import requests
import json

BASE_URL = "http://localhost:5000/api/data"  # 您的 Flask 服务的 API 基地址

def create_new_data(name, value):
    """向服务器发送 POST 请求以创建新数据"""
    payload = {
        "name": name,
        "value": value
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # 如果状态码是 4xx 或 5xx，则抛出 HTTPError
        created_item = response.json()
        print(f"创建成功: {created_item}")
        return created_item
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (创建数据时): {http_err}")
        print(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (创建数据时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (创建数据时): {e}")
    return None

def get_all_data():
    """向服务器发送 GET 请求以获取所有数据"""
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        all_items = response.json()
        print(f"获取到的所有数据: {json.dumps(all_items, indent=2, ensure_ascii=False)}")
        return all_items
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (获取所有数据时): {http_err}")
        print(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (获取所有数据时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (获取所有数据时): {e}")
    return None

def get_specific_data(item_id):
    """向服务器发送 GET 请求以获取特定 ID 的数据"""
    url = f"{BASE_URL}/{item_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        item = response.json()
        print(f"获取到的特定数据 (ID: {item_id}): {json.dumps(item, indent=2, ensure_ascii=False)}")
        return item
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (获取特定数据 ID: {item_id} 时): {http_err}")
        print(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (获取特定数据 ID: {item_id} 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (获取特定数据 ID: {item_id} 时): {e}")
    return None

def update_existing_data(item_id, new_name, new_value):
    """向服务器发送 PUT 请求以更新特定 ID 的数据"""
    url = f"{BASE_URL}/{item_id}"
    payload = {
        "name": new_name,
        "value": new_value
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        updated_item = response.json()
        print(f"更新成功 (ID: {item_id}): {updated_item}")
        return updated_item
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (更新数据 ID: {item_id} 时): {http_err}")
        print(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (更新数据 ID: {item_id} 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (更新数据 ID: {item_id} 时): {e}")
    return None

def delete_specific_data(item_id):
    """向服务器发送 DELETE 请求以删除特定 ID 的数据"""
    url = f"{BASE_URL}/{item_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        # DELETE 请求成功通常返回 200 OK 或 204 No Content，以及一个消息
        # Flask 应用中返回的是 JSON 消息和 200
        message = response.json()
        print(f"删除成功 (ID: {item_id}): {message}")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (删除数据 ID: {item_id} 时): {http_err}")
        print(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (删除数据 ID: {item_id} 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (删除数据 ID: {item_id} 时): {e}")
    return False

if __name__ == "__main__":
    print("--- 开始测试与 Flask Web Service 的交互 ---")

    # 1. 创建一些新数据
    print("\\n--- 1. 测试创建数据 ---")
    item1 = create_new_data("测试项目A", "这是项目A的值")
    item2 = create_new_data("测试项目B", "这是项目B的一些描述")
    
    created_item_id = None
    if item1:
        created_item_id = item1.get('id')

    # 2. 获取所有数据
    print("\\n--- 2. 测试获取所有数据 ---")
    all_data_list = get_all_data()

    # 3. 获取一条特定数据 (如果上一条创建成功)
    if created_item_id:
        print(f"\\n--- 3. 测试获取特定数据 (ID: {created_item_id}) ---")
        get_specific_data(created_item_id)
    else:
        print("\\n--- 3. 跳过获取特定数据 (因为没有成功创建的条目ID) ---")

    # 4. 更新一条特定数据 (如果上一条创建成功)
    if created_item_id:
        print(f"\\n--- 4. 测试更新特定数据 (ID: {created_item_id}) ---")
        update_existing_data(created_item_id, "更新后的项目A", "项目A的值已被更新")
        # 再次获取该数据以查看更新
        get_specific_data(created_item_id)
    else:
        print("\\n--- 4. 跳过更新特定数据 (因为没有成功创建的条目ID) ---")

    # 5. 删除一条特定数据 (如果上一条创建成功)
    if created_item_id:
        print(f"\\n--- 5. 测试删除特定数据 (ID: {created_item_id}) ---")
        delete_specific_data(created_item_id)
        # 尝试再次获取已删除的数据 (应该会失败或返回404)
        print(f"尝试获取已删除的数据 (ID: {created_item_id}):")
        get_specific_data(created_item_id)
        # 再次获取所有数据查看变化
        get_all_data()
    else:
        print("\\n--- 5. 跳过删除特定数据 (因为没有成功创建的条目ID) ---")
        
    # 尝试获取一个不存在的数据
    print("\\n--- 6. 测试获取不存在的数据 ---")
    get_specific_data(99999) # 假设这个ID不存在

    print("\\n--- 测试结束 ---")
