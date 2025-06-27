import requests
import json
import uuid
import random
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api/wifi_board_tests"  # API base address for wifi_board_tests

def create_new_wifi_test(wifi_board_sn, knob_result="PENDING", knob_remark="", network_result="PENDING", network_remark=""):
    """Sends a POST request to create a new wifi board test record."""
    payload = {
        "wifi_board_sn": wifi_board_sn,  # 修正字段名
        "general_test_result": "PENDING",
        
        # 旋钮测试相关
        "knob_test_result": knob_result,
        "speed_knob_result": "PENDING",
        "time_knob_result": "PENDING",
        
        # 灯光测试相关
        "light_test_result": "PENDING",
        "green_light_result": "PENDING",
        "red_light_result": "PENDING",
        "blue_light_result": "PENDING",
        
        # 网络测试相关
        "network_test_result": network_result,
        "wifi_software_version": "v1.0.0",
        "start_command_result": "SUCCESS",
        "speed_command_result": "SUCCESS",
        "stop_command_result": "SUCCESS",
        
        # 通用信息
        "test_ip_address": "192.168.1.100",
        "general_test_remark": knob_remark + " " + network_remark
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        created_item = response.json()
        return created_item
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (创建 WiFi Board Test 时): {http_err}")
        print(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (创建 WiFi Board Test 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (创建 WiFi Board Test 时): {e}")
    return None

def create_batch_test_data(count=50):
    """批量创建多样化的测试数据"""
    print(f"开始批量创建 {count} 条测试数据...")
    
    # 预定义的测试状态选项
    test_results = ["PASSED", "FAILED", "PENDING", "SKIPPED", "TIMEOUT"]
    knob_results = ["PASSED", "FAILED", "PENDING", "PARTIAL_FAIL"]
    light_results = ["PASSED", "FAILED", "PENDING", "FLICKERING"]
    network_results = ["PASSED", "FAILED", "PENDING", "WEAK_SIGNAL", "TIMEOUT"]
    
    # 预定义的 WiFi 软件版本
    wifi_versions = ["v1.0.0", "v1.0.1", "v1.1.0", "v1.2.0", "v2.0.0", "v2.1.0"]
    
    # 预定义的 IP 地址段
    ip_ranges = ["192.168.1", "192.168.2", "10.0.0", "172.16.1"]
    
    # 预定义的测试备注
    knob_remarks = [
        "All knobs working properly",
        "Speed knob stuck at 50%",
        "Time knob not responding",
        "Knob rotation inconsistent",
        "Knob LED not lighting up",
        "Normal operation detected",
        "Mechanical resistance detected"
    ]
    
    light_remarks = [
        "All lights functioning normally",
        "Red light dim",
        "Blue light flickering",
        "Green light not responding",
        "RGB color mixing issues",
        "LED driver problem",
        "Normal illumination"
    ]
    
    network_remarks = [
        "Connected to AP_TEST_01",
        "Connection timeout",
        "DHCP assignment failed",
        "Weak signal strength",
        "Intermittent disconnection",
        "DNS resolution failed",
        "Normal network operation"
    ]
    
    created_items = []
    
    for i in range(count):
        # 生成随机的序列号
        sn_prefix = random.choice(["WB", "WIFI", "TEST"])
        sn_suffix = f"{random.randint(1000, 9999):04d}"
        wifi_board_sn = f"{sn_prefix}_{sn_suffix}"
        
        # 随机选择测试结果
        general_result = random.choice(test_results)
        knob_result = random.choice(knob_results)
        speed_knob_result = random.choice(knob_results)
        time_knob_result = random.choice(knob_results)
        
        light_result = random.choice(light_results)
        green_light_result = random.choice(light_results)
        red_light_result = random.choice(light_results)
        blue_light_result = random.choice(light_results)
        
        network_result = random.choice(network_results)
        start_command_result = random.choice(["SUCCESS", "FAILED", "TIMEOUT"])
        speed_command_result = random.choice(["SUCCESS", "FAILED", "TIMEOUT"])
        stop_command_result = random.choice(["SUCCESS", "FAILED", "TIMEOUT"])
        
        # 随机选择其他参数
        wifi_version = random.choice(wifi_versions)
        ip_base = random.choice(ip_ranges)
        ip_address = f"{ip_base}.{random.randint(100, 200)}"
        
        knob_remark = random.choice(knob_remarks)
        light_remark = random.choice(light_remarks)
        network_remark = random.choice(network_remarks)
        
        # 创建测试数据
        payload = {
            "wifi_board_sn": wifi_board_sn,
            "general_test_result": general_result,
            
            # 旋钮测试相关
            "knob_test_result": knob_result,
            "speed_knob_result": speed_knob_result,
            "time_knob_result": time_knob_result,
            
            # 灯光测试相关
            "light_test_result": light_result,
            "green_light_result": green_light_result,
            "red_light_result": red_light_result,
            "blue_light_result": blue_light_result,
            
            # 网络测试相关
            "network_test_result": network_result,
            "wifi_software_version": wifi_version,
            "start_command_result": start_command_result,
            "speed_command_result": speed_command_result,
            "stop_command_result": stop_command_result,
            
            # 通用信息
            "test_ip_address": ip_address,
            "general_test_remark": f"{knob_remark} | {light_remark} | {network_remark}"
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            created_item = response.json()
            created_items.append(created_item)
            
            # 每创建10条记录打印一次进度
            if (i + 1) % 10 == 0:
                print(f"已创建 {i + 1}/{count} 条记录...")
                
        except Exception as e:
            print(f"创建第 {i + 1} 条记录失败: {e}")
    
    print(f"批量创建完成，成功创建 {len(created_items)} 条记录")
    return created_items

def get_all_wifi_tests():
    """Sends a GET request to retrieve all wifi board test records."""
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        result = response.json()
        
        # 处理新的分页响应格式
        if isinstance(result, dict) and 'data' in result:
            all_items = result['data']
            pagination = result.get('pagination', {})
            print(f"获取到 {len(all_items)} 条 WiFi Board Tests (总共 {pagination.get('total', 'N/A')} 条):")
            return result
        else:
            # 兼容旧格式
            all_items = result if isinstance(result, list) else []
            print(f"获取到的所有 WiFi Board Tests: 共 {len(all_items)} 条记录")
            return result
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (获取所有 WiFi Board Tests 时): {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (获取所有 WiFi Board Tests 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (获取所有 WiFi Board Tests 时): {e}")
    return None

def get_specific_wifi_test(item_id):
    """Sends a GET request to retrieve a specific wifi board test record by ID."""
    url = f"{BASE_URL}/{item_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        item = response.json()
        print(f"获取到的特定 WiFi Board Test (ID: {item_id}): SN={item.get('wifi_board_sn', 'N/A')}")
        return item
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (获取特定 WiFi Board Test ID: {item_id} 时): {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (获取特定 WiFi Board Test ID: {item_id} 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (获取特定 WiFi Board Test ID: {item_id} 时): {e}")
    return None

def update_existing_wifi_test(item_id, wifi_board_sn, knob_result="UPDATED", knob_remark="Updated remark"):
    """Sends a PUT request to update a specific wifi board test record."""
    url = f"{BASE_URL}/{item_id}"
    payload = {
        "wifi_board_sn": wifi_board_sn,
        "general_test_result": "FAILED",
        
        # 旋钮测试相关
        "knob_test_result": knob_result,
        "speed_knob_result": "PASSED",
        "time_knob_result": "FAILED",
        
        # 灯光测试相关
        "light_test_result": "PASSED",
        "green_light_result": "PASSED",
        "red_light_result": "PASSED", 
        "blue_light_result": "FAILED",
        
        # 网络测试相关
        "network_test_result": "FAILED",
        "wifi_software_version": "v1.0.1",
        "start_command_result": "SUCCESS",
        "speed_command_result": "FAILED",
        "stop_command_result": "SUCCESS",
        
        # 通用信息
        "test_ip_address": "192.168.1.101",
        "general_test_remark": f"{knob_remark} - WiFi module unresponsive after update."
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        updated_item = response.json()
        print(f"更新成功 (WiFi Board Test ID: {item_id})")
        return updated_item
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (更新 WiFi Board Test ID: {item_id} 时): {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (更新 WiFi Board Test ID: {item_id} 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (更新 WiFi Board Test ID: {item_id} 时): {e}")
    return None

def delete_specific_wifi_test(item_id):
    """Sends a DELETE request to delete a specific wifi board test record."""
    url = f"{BASE_URL}/{item_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        message = response.json()
        print(f"删除成功 (WiFi Board Test ID: {item_id})")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (删除 WiFi Board Test ID: {item_id} 时): {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (删除 WiFi Board Test ID: {item_id} 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (删除 WiFi Board Test ID: {item_id} 时): {e}")
    return False

def test_advanced_features():
    """测试高级功能：分页、排序、筛选"""
    print("\n=== 测试高级功能 ===")
    
    # 1. 测试分页功能
    print("\n1. 测试分页功能:")
    page_sizes = [5, 10, 20]
    for per_page in page_sizes:
        try:
            response = requests.get(f"{BASE_URL}?page=1&per_page={per_page}")
            response.raise_for_status()
            result = response.json()
            data_count = len(result.get('data', []))
            total = result.get('pagination', {}).get('total', 0)
            print(f"  每页 {per_page} 条: 获取到 {data_count} 条记录，总共 {total} 条")
        except Exception as e:
            print(f"  分页测试失败 (per_page={per_page}): {e}")
    
    # 2. 测试排序功能
    print("\n2. 测试排序功能:")
    sort_fields = ['wifi_board_sn', 'general_test_result', 'update_time']
    for field in sort_fields:
        for order in ['asc', 'desc']:
            try:
                response = requests.get(f"{BASE_URL}?sort_by={field}&sort_order={order}&per_page=5")
                response.raise_for_status()
                result = response.json()
                data_count = len(result.get('data', []))
                print(f"  按 {field} {order} 排序: 获取到 {data_count} 条记录")
                
                # 显示前3条记录的排序字段值
                if data_count > 0:
                    items = result.get('data', [])[:3]
                    values = [item.get(field, 'N/A') for item in items]
                    print(f"    前3条 {field} 值: {values}")
                    
            except Exception as e:
                print(f"  排序测试失败 ({field} {order}): {e}")
    
    # 3. 测试筛选功能
    print("\n3. 测试筛选功能:")
    filter_tests = [
        ('general_test_result', 'PASSED'),
        ('general_test_result', 'FAILED'),
        ('general_test_result', 'PENDING'),
        ('wifi_board_sn', 'WB'),
        ('wifi_board_sn', 'WIFI'),
        ('wifi_board_sn', 'TEST')
    ]
    
    for field, value in filter_tests:
        try:
            if field == 'wifi_board_sn':
                # 使用模糊查询
                response = requests.get(f"{BASE_URL}?{field}={value}&per_page=5")
            else:
                # 使用精确查询
                response = requests.get(f"{BASE_URL}?{field}={value}&per_page=5")
                
            response.raise_for_status()
            result = response.json()
            data_count = len(result.get('data', []))
            total = result.get('pagination', {}).get('total', 0)
            print(f"  {field}={value}: 获取到 {data_count} 条记录，总匹配 {total} 条")
            
        except Exception as e:
            print(f"  筛选测试失败 ({field}={value}): {e}")
    
    # 4. 测试复合查询
    print("\n4. 测试复合查询 (分页+排序+筛选):")
    try:
        response = requests.get(f"{BASE_URL}?general_test_result=PASSED&sort_by=wifi_board_sn&sort_order=asc&page=1&per_page=3")
        response.raise_for_status()
        result = response.json()
        data_count = len(result.get('data', []))
        total = result.get('pagination', {}).get('total', 0)
        print(f"  复合查询结果: 获取到 {data_count} 条记录，总匹配 {total} 条")
        
        # 显示结果
        if data_count > 0:
            items = result.get('data', [])
            for item in items:
                sn = item.get('wifi_board_sn', 'N/A')
                status = item.get('general_test_result', 'N/A')
                print(f"    SN: {sn}, Status: {status}")
                
    except Exception as e:
        print(f"  复合查询测试失败: {e}")

def test_data_distribution():
    """测试数据分布情况"""
    print("\n=== 数据分布分析 ===")
    
    try:
        # 获取所有数据
        response = requests.get(f"{BASE_URL}?per_page=100")
        response.raise_for_status()
        result = response.json()
        all_items = result.get('data', [])
        total = result.get('pagination', {}).get('total', 0)
        
        print(f"总记录数: {total}")
        print(f"当前页记录数: {len(all_items)}")
        
        if len(all_items) > 0:
            # 分析测试结果分布
            status_count = {}
            version_count = {}
            sn_prefix_count = {}
            
            for item in all_items:
                # 统计测试结果分布
                status = item.get('general_test_result', 'UNKNOWN')
                status_count[status] = status_count.get(status, 0) + 1
                
                # 统计版本分布
                version = item.get('wifi_software_version', 'UNKNOWN')
                version_count[version] = version_count.get(version, 0) + 1
                
                # 统计SN前缀分布
                sn = item.get('wifi_board_sn', '')
                prefix = sn.split('_')[0] if '_' in sn else sn[:3]
                sn_prefix_count[prefix] = sn_prefix_count.get(prefix, 0) + 1
            
            print("\n测试结果分布:")
            for status, count in sorted(status_count.items()):
                percentage = (count / len(all_items)) * 100
                print(f"  {status}: {count} 条 ({percentage:.1f}%)")
            
            print("\n软件版本分布:")
            for version, count in sorted(version_count.items()):
                percentage = (count / len(all_items)) * 100
                print(f"  {version}: {count} 条 ({percentage:.1f}%)")
            
            print("\nSN前缀分布:")
            for prefix, count in sorted(sn_prefix_count.items()):
                percentage = (count / len(all_items)) * 100
                print(f"  {prefix}: {count} 条 ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"数据分布分析失败: {e}")

if __name__ == "__main__":
    print("=== 开始测试与 Flask Web Service (WiFi Board Tests) 的交互 ===")

    # 1. 批量创建测试数据
    print("\n1. 批量创建测试数据")
    created_items = create_batch_test_data(30)  # 创建30条测试数据
    
    # 2. 获取所有测试记录概览
    print("\n2. 获取所有测试记录概览")
    all_data = get_all_wifi_tests()
    
    # 3. 数据分布分析
    test_data_distribution()
    
    # 4. 测试高级功能
    test_advanced_features()
    
    # 5. 测试单条记录操作
    if created_items and len(created_items) > 0:
        test_item = created_items[0]
        item_id = test_item.get('id')
        
        print(f"\n5. 测试单条记录操作 (ID: {item_id})")
        
        # 获取特定记录
        print("  获取特定记录:")
        get_specific_wifi_test(item_id)
        
        # 更新记录
        print("  更新记录:")
        update_existing_wifi_test(
            item_id, 
            test_item.get('wifi_board_sn'), 
            knob_result="RETEST_PASSED", 
            knob_remark="Updated after batch creation"
        )
        
        # 验证更新
        print("  验证更新:")
        get_specific_wifi_test(item_id)
        
        # 删除记录
        print("  删除记录:")
        delete_specific_wifi_test(item_id)
        
        # 验证删除
        print("  验证删除:")
        get_specific_wifi_test(item_id)
    
    # 6. 测试边界情况
    print("\n6. 测试边界情况")
    
    # 测试不存在的记录
    print("  测试不存在的记录:")
    fake_id = "01HN2P3Q4R5S6T7U8V9W0X1Y2Z"
    get_specific_wifi_test(fake_id)
    
    # 测试大页面
    print("  测试大页面查询:")
    try:
        response = requests.get(f"{BASE_URL}?page=999&per_page=10")
        response.raise_for_status()
        result = response.json()
        print(f"    大页面查询结果: {len(result.get('data', []))} 条记录")
    except Exception as e:
        print(f"    大页面查询失败: {e}")
    
    # 测试无效排序字段
    print("  测试无效排序字段:")
    try:
        response = requests.get(f"{BASE_URL}?sort_by=invalid_field&per_page=5")
        response.raise_for_status()
        result = response.json()
        print(f"    无效排序字段查询结果: {len(result.get('data', []))} 条记录")
    except Exception as e:
        print(f"    无效排序字段查询失败: {e}")

    print("\n=== WiFi Board Test 交互测试结束 ===")
