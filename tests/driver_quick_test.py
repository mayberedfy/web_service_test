import requests
import json
import uuid
import random
from datetime import datetime, timedelta

BASE_URL = "http://121.196.236.235:5000/api/driver_board_tests"  # API base address for driver_board_tests

def create_new_driver_test(driver_board_sn, motor_result="PENDING", motor_remark="", power_result="PENDING", power_remark=""):
    """Sends a POST request to create a new driver board test record."""
    payload = {
        "driver_board_sn": driver_board_sn,
        "general_test_result": "PENDING",
        
        # 测试结果字段（是否通过测试）
        "motor_status_result": motor_result,
        "motor_speed_result": "PENDING",
        "ipm_temperature_result": "PENDING",
        "dc_voltage_result": "PENDING",
        "output_power_result": power_result,
        "driver_software_version_result": "PENDING",
        
        # 测试数值字段（实际测试数据）
        "motor_status": "IDLE",
        "motor_speed": "0",
        "ipm_temperature": "25.0",
        "dc_voltage": "48.0",
        "output_power": "0.0",
        "driver_software_version": "v1.0.0",
        
        # 测试运行信息
        "test_runtime": 60,
        "test_ip_address": "192.168.1.100",
        "general_test_remark": motor_remark + " " + power_remark
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
        print(f"HTTP 错误 (创建 Driver Board Test 时): {http_err}")
        print(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (创建 Driver Board Test 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (创建 Driver Board Test 时): {e}")
    return None

def create_batch_test_data(count=50):
    """批量创建多样化的驱动板测试数据"""
    print(f"开始批量创建 {count} 条驱动板测试数据...")
    
    # 预定义的测试状态选项
    test_results = ["PASSED", "FAILED", "PENDING", "SKIPPED", "TIMEOUT"]
    motor_results = ["PASSED", "FAILED", "PENDING", "OVERLOAD", "STALL"]
    temperature_results = ["PASSED", "FAILED", "PENDING", "OVERHEAT", "UNDERHEAT"]
    voltage_results = ["PASSED", "FAILED", "PENDING", "OVERVOLTAGE", "UNDERVOLTAGE"]
    power_results = ["PASSED", "FAILED", "PENDING", "OVERPOWER", "UNDERPOWER"]
    
    # 预定义的驱动板软件版本
    driver_versions = ["v1.0.0", "v1.0.1", "v1.1.0", "v1.2.0", "v2.0.0", "v2.1.0"]
    
    # 预定义的 IP 地址段
    ip_ranges = ["192.168.1", "192.168.2", "10.0.0", "172.16.1"]
    
    # 预定义的电机状态
    motor_statuses = ["IDLE", "RUNNING", "STOPPED", "ERROR", "LOCKED"]
    
    # 预定义的测试备注
    motor_remarks = [
        "Motor running smoothly",
        "Motor vibration detected",
        "Motor locked during test",
        "Motor speed inconsistent",
        "Motor temperature high",
        "Normal motor operation",
        "Motor overcurrent detected"
    ]
    
    power_remarks = [
        "Power output stable",
        "Power fluctuation detected",
        "DC voltage unstable",
        "IPM temperature normal",
        "Power efficiency good",
        "Voltage regulation failed",
        "Normal power operation"
    ]
    
    driver_remarks = [
        "Driver board functioning normally",
        "Communication timeout",
        "Sensor reading error",
        "Control loop unstable",
        "Thermal protection activated",
        "Normal driver operation",
        "Firmware update required"
    ]
    
    created_items = []
    
    for i in range(count):
        # 生成随机的序列号
        sn_prefix = random.choice(["DB", "DRV", "DRIVER"])
        sn_suffix = f"{random.randint(1000, 9999):04d}"
        driver_board_sn = f"{sn_prefix}_{sn_suffix}"
        
        # 随机选择测试结果
        general_result = random.choice(test_results)
        motor_status_result = random.choice(motor_results)
        motor_speed_result = random.choice(motor_results)
        ipm_temperature_result = random.choice(temperature_results)
        dc_voltage_result = random.choice(voltage_results)
        output_power_result = random.choice(power_results)
        driver_software_version_result = random.choice(test_results)
        
        # 随机选择实际测试数值
        motor_status = random.choice(motor_statuses)
        motor_speed = str(random.randint(0, 3000))  # 0-3000 RPM
        ipm_temperature = f"{random.uniform(20.0, 80.0):.1f}"  # 20-80°C
        dc_voltage = f"{random.uniform(40.0, 60.0):.1f}"  # 40-60V
        output_power = f"{random.uniform(0.0, 5.0):.2f}"  # 0-5kW
        driver_version = random.choice(driver_versions)
        
        # 随机选择其他参数
        test_runtime = random.randint(30, 300)  # 30-300秒
        ip_base = random.choice(ip_ranges)
        ip_address = f"{ip_base}.{random.randint(100, 200)}"
        
        motor_remark = random.choice(motor_remarks)
        power_remark = random.choice(power_remarks)
        driver_remark = random.choice(driver_remarks)
        
        # 创建测试数据
        payload = {
            "driver_board_sn": driver_board_sn,
            "general_test_result": general_result,
            
            # 测试结果字段（是否通过测试）
            "motor_status_result": motor_status_result,
            "motor_speed_result": motor_speed_result,
            "ipm_temperature_result": ipm_temperature_result,
            "dc_voltage_result": dc_voltage_result,
            "output_power_result": output_power_result,
            "driver_software_version_result": driver_software_version_result,
            
            # 测试数值字段（实际测试数据）
            "motor_status": motor_status,
            "motor_speed": motor_speed,
            "ipm_temperature": ipm_temperature,
            "dc_voltage": dc_voltage,
            "output_power": output_power,
            "driver_software_version": driver_version,
            
            # 测试运行信息
            "test_runtime": test_runtime,
            "test_ip_address": ip_address,
            "general_test_remark": f"{motor_remark} | {power_remark} | {driver_remark}"
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

def get_all_driver_tests():
    """Sends a GET request to retrieve all driver board test records."""
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        result = response.json()
        
        # 处理新的分页响应格式
        if isinstance(result, dict) and 'data' in result:
            all_items = result['data']
            pagination = result.get('pagination', {})
            print(f"获取到 {len(all_items)} 条 Driver Board Tests (总共 {pagination.get('total', 'N/A')} 条):")
            return result
        else:
            # 兼容旧格式
            all_items = result if isinstance(result, list) else []
            print(f"获取到的所有 Driver Board Tests: 共 {len(all_items)} 条记录")
            return result
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (获取所有 Driver Board Tests 时): {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (获取所有 Driver Board Tests 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (获取所有 Driver Board Tests 时): {e}")
    return None

def get_specific_driver_test(item_id):
    """Sends a GET request to retrieve a specific driver board test record by ID."""
    url = f"{BASE_URL}/{item_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        item = response.json()
        print(f"获取到的特定 Driver Board Test (ID: {item_id}): SN={item.get('driver_board_sn', 'N/A')}")
        return item
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (获取特定 Driver Board Test ID: {item_id} 时): {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (获取特定 Driver Board Test ID: {item_id} 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (获取特定 Driver Board Test ID: {item_id} 时): {e}")
    return None

def update_existing_driver_test(item_id, driver_board_sn, motor_result="UPDATED", motor_remark="Updated remark"):
    """Sends a PUT request to update a specific driver board test record."""
    url = f"{BASE_URL}/{item_id}"
    payload = {
        "driver_board_sn": driver_board_sn,
        "general_test_result": "FAILED",
        
        # 测试结果字段（是否通过测试）
        "motor_status_result": motor_result,
        "motor_speed_result": "PASSED",
        "ipm_temperature_result": "FAILED",
        "dc_voltage_result": "PASSED",
        "output_power_result": "FAILED",
        "driver_software_version_result": "PASSED",
        
        # 测试数值字段（实际测试数据）
        "motor_status": "ERROR",
        "motor_speed": "0",
        "ipm_temperature": "85.5",
        "dc_voltage": "48.2",
        "output_power": "0.1",
        "driver_software_version": "v1.0.1",
        
        # 测试运行信息
        "test_runtime": 180,
        "test_ip_address": "192.168.1.101",
        "general_test_remark": f"{motor_remark} - Motor overheated during test."
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        updated_item = response.json()
        print(f"更新成功 (Driver Board Test ID: {item_id})")
        return updated_item
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (更新 Driver Board Test ID: {item_id} 时): {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (更新 Driver Board Test ID: {item_id} 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (更新 Driver Board Test ID: {item_id} 时): {e}")
    return None

def delete_specific_driver_test(item_id):
    """Sends a DELETE request to delete a specific driver board test record."""
    url = f"{BASE_URL}/{item_id}"
    try:
        response = requests.delete(url)
        response.raise_for_status()
        message = response.json()
        print(f"删除成功 (Driver Board Test ID: {item_id})")
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误 (删除 Driver Board Test ID: {item_id} 时): {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误 (删除 Driver Board Test ID: {item_id} 时): {req_err}")
    except Exception as e:
        print(f"发生未知错误 (删除 Driver Board Test ID: {item_id} 时): {e}")
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
    sort_fields = ['driver_board_sn', 'general_test_result', 'update_time', 'test_runtime']
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
        ('driver_board_sn', 'DB'),
        ('driver_board_sn', 'DRV'),
        ('driver_board_sn', 'DRIVER')
    ]
    
    for field, value in filter_tests:
        try:
            if field == 'driver_board_sn':
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
        response = requests.get(f"{BASE_URL}?general_test_result=PASSED&sort_by=driver_board_sn&sort_order=asc&page=1&per_page=3")
        response.raise_for_status()
        result = response.json()
        data_count = len(result.get('data', []))
        total = result.get('pagination', {}).get('total', 0)
        print(f"  复合查询结果: 获取到 {data_count} 条记录，总匹配 {total} 条")
        
        # 显示结果
        if data_count > 0:
            items = result.get('data', [])
            for item in items:
                sn = item.get('driver_board_sn', 'N/A')
                status = item.get('general_test_result', 'N/A')
                runtime = item.get('test_runtime', 'N/A')
                print(f"    SN: {sn}, Status: {status}, Runtime: {runtime}s")
                
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
            motor_status_count = {}
            
            for item in all_items:
                # 统计测试结果分布
                status = item.get('general_test_result', 'UNKNOWN')
                status_count[status] = status_count.get(status, 0) + 1
                
                # 统计版本分布
                version = item.get('driver_software_version', 'UNKNOWN')
                version_count[version] = version_count.get(version, 0) + 1
                
                # 统计SN前缀分布
                sn = item.get('driver_board_sn', '')
                prefix = sn.split('_')[0] if '_' in sn else sn[:3]
                sn_prefix_count[prefix] = sn_prefix_count.get(prefix, 0) + 1
                
                # 统计电机状态分布
                motor_status = item.get('motor_status', 'UNKNOWN')
                motor_status_count[motor_status] = motor_status_count.get(motor_status, 0) + 1
            
            print("\n测试结果分布:")
            for status, count in sorted(status_count.items()):
                percentage = (count / len(all_items)) * 100
                print(f"  {status}: {count} 条 ({percentage:.1f}%)")
            
            print("\n驱动板软件版本分布:")
            for version, count in sorted(version_count.items()):
                percentage = (count / len(all_items)) * 100
                print(f"  {version}: {count} 条 ({percentage:.1f}%)")
            
            print("\nSN前缀分布:")
            for prefix, count in sorted(sn_prefix_count.items()):
                percentage = (count / len(all_items)) * 100
                print(f"  {prefix}: {count} 条 ({percentage:.1f}%)")
            
            print("\n电机状态分布:")
            for motor_status, count in sorted(motor_status_count.items()):
                percentage = (count / len(all_items)) * 100
                print(f"  {motor_status}: {count} 条 ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"数据分布分析失败: {e}")

def test_performance_metrics():
    """测试性能相关数据分析"""
    print("\n=== 性能数据分析 ===")
    
    try:
        # 获取所有数据
        response = requests.get(f"{BASE_URL}?per_page=100")
        response.raise_for_status()
        result = response.json()
        all_items = result.get('data', [])
        
        if len(all_items) > 0:
            # 收集性能数据
            runtimes = []
            motor_speeds = []
            temperatures = []
            voltages = []
            powers = []
            
            for item in all_items:
                # 收集运行时间
                runtime = item.get('test_runtime')
                if runtime is not None:
                    runtimes.append(runtime)
                
                # 收集电机转速
                speed = item.get('motor_speed')
                if speed and speed.replace('.', '').isdigit():
                    motor_speeds.append(float(speed))
                
                # 收集温度
                temp = item.get('ipm_temperature')
                if temp and temp.replace('.', '').isdigit():
                    temperatures.append(float(temp))
                
                # 收集电压
                voltage = item.get('dc_voltage')
                if voltage and voltage.replace('.', '').isdigit():
                    voltages.append(float(voltage))
                
                # 收集功率
                power = item.get('output_power')
                if power and power.replace('.', '').isdigit():
                    powers.append(float(power))
            
            # 计算统计数据
            if runtimes:
                print(f"\n测试运行时间统计:")
                print(f"  平均运行时间: {sum(runtimes)/len(runtimes):.1f}s")
                print(f"  最短运行时间: {min(runtimes)}s")
                print(f"  最长运行时间: {max(runtimes)}s")
            
            if motor_speeds:
                print(f"\n电机转速统计:")
                print(f"  平均转速: {sum(motor_speeds)/len(motor_speeds):.1f} RPM")
                print(f"  最低转速: {min(motor_speeds)} RPM")
                print(f"  最高转速: {max(motor_speeds)} RPM")
            
            if temperatures:
                print(f"\nIPM温度统计:")
                print(f"  平均温度: {sum(temperatures)/len(temperatures):.1f}°C")
                print(f"  最低温度: {min(temperatures)}°C")
                print(f"  最高温度: {max(temperatures)}°C")
            
            if voltages:
                print(f"\nDC电压统计:")
                print(f"  平均电压: {sum(voltages)/len(voltages):.1f}V")
                print(f"  最低电压: {min(voltages)}V")
                print(f"  最高电压: {max(voltages)}V")
            
            if powers:
                print(f"\n输出功率统计:")
                print(f"  平均功率: {sum(powers)/len(powers):.2f}kW")
                print(f"  最低功率: {min(powers)}kW")
                print(f"  最高功率: {max(powers)}kW")
        
    except Exception as e:
        print(f"性能数据分析失败: {e}")

if __name__ == "__main__":
    print("=== 开始测试与 Flask Web Service (Driver Board Tests) 的交互 ===")

    # 1. 批量创建测试数据
    print("\n1. 批量创建驱动板测试数据")
    created_items = create_batch_test_data(40)  # 创建40条测试数据
    
    # 2. 获取所有测试记录概览
    print("\n2. 获取所有测试记录概览")
    all_data = get_all_driver_tests()
    
    # 3. 数据分布分析
    test_data_distribution()
    
    # 4. 性能数据分析
    test_performance_metrics()
    
    # 5. 测试高级功能
    test_advanced_features()
    
    # 6. 测试单条记录操作
    if created_items and len(created_items) > 0:
        test_item = created_items[0]
        item_id = test_item.get('id')
        
        print(f"\n6. 测试单条记录操作 (ID: {item_id})")
        
        # 获取特定记录
        print("  获取特定记录:")
        get_specific_driver_test(item_id)
        
        # 更新记录
        print("  更新记录:")
        update_existing_driver_test(
            item_id, 
            test_item.get('driver_board_sn'), 
            motor_result="RETEST_PASSED", 
            motor_remark="Updated after batch creation"
        )
        
        # 验证更新
        print("  验证更新:")
        get_specific_driver_test(item_id)
        
        # 删除记录
        print("  删除记录:")
        delete_specific_driver_test(item_id)
        
        # 验证删除
        print("  验证删除:")
        get_specific_driver_test(item_id)
    
    # 7. 测试边界情况
    print("\n7. 测试边界情况")
    
    # 测试不存在的记录
    print("  测试不存在的记录:")
    fake_id = "01HN2P3Q4R5S6T7U8V9W0X1Y2Z"
    get_specific_driver_test(fake_id)
    
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
    
    # 测试运行时间筛选
    print("  测试性能数据筛选:")
    try:
        # 虽然API可能不直接支持数值范围筛选，但我们可以测试基本查询
        response = requests.get(f"{BASE_URL}?per_page=10")
        response.raise_for_status()
        result = response.json()
        items = result.get('data', [])
        if items:
            print(f"    获取到 {len(items)} 条记录用于性能分析")
            for item in items[:3]:  # 显示前3条记录的关键性能指标
                sn = item.get('driver_board_sn', 'N/A')
                runtime = item.get('test_runtime', 'N/A')
                motor_speed = item.get('motor_speed', 'N/A')
                temperature = item.get('ipm_temperature', 'N/A')
                print(f"      SN: {sn}, Runtime: {runtime}s, Speed: {motor_speed}RPM, Temp: {temperature}°C")
    except Exception as e:
        print(f"    性能数据筛选失败: {e}")

    print("\n=== Driver Board Test 交互测试结束 ===")