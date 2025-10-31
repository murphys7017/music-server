"""
测试认证中间件
演示如何使用 Token 认证
"""
import requests

BASE_URL = "http://localhost:8000"
TOKEN = "your_static_token_here"  # 修改为你的 .env 中的 STATIC_TOKEN

print("=" * 60)
print("测试 Token 认证中间件")
print("=" * 60)

# 测试1: 访问不需要认证的路径（根路径）
print("\n1. 测试白名单路径（不需要认证）")
print(f"GET {BASE_URL}/")
try:
    r = requests.get(f"{BASE_URL}/")
    print(f"  状态码: {r.status_code}")
    print(f"  响应: {r.json()}")
except Exception as e:
    print(f"  错误: {e}")

# 测试2: 不带 Token 访问需要认证的接口
print("\n2. 测试未提供 Token")
print(f"GET {BASE_URL}/music/list")
try:
    r = requests.get(f"{BASE_URL}/music/list")
    print(f"  状态码: {r.status_code}")
    if r.status_code == 401:
        print(f"  ✅ 认证拒绝成功")
        try:
            print(f"  响应: {r.json()}")
        except:
            print(f"  响应文本: {r.text}")
    else:
        print(f"  响应: {r.json()}")
except Exception as e:
    print(f"  错误: {e}")

# 测试3: 使用错误的 Token
print("\n3. 测试错误的 Token")
print(f"GET {BASE_URL}/music/list")
headers = {"Authorization": "Bearer wrong_token"}
try:
    r = requests.get(f"{BASE_URL}/music/list", headers=headers)
    print(f"  状态码: {r.status_code}")
    if r.status_code == 401:
        print(f"  ✅ 认证拒绝成功")
        try:
            print(f"  响应: {r.json()}")
        except:
            print(f"  响应文本: {r.text}")
    else:
        print(f"  响应: {r.json()}")
except Exception as e:
    print(f"  错误: {e}")

# 测试4: 使用正确的 Token
print("\n4. 测试正确的 Token")
print(f"GET {BASE_URL}/music/list?page=1&page_size=2")
headers = {"Authorization": f"Bearer {TOKEN}"}
try:
    r = requests.get(f"{BASE_URL}/music/list?page=1&page_size=2", headers=headers)
    print(f"  状态码: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  响应: code={data['code']}, total={data['data']['total']}")
    else:
        print(f"  响应: {r.json()}")
except Exception as e:
    print(f"  错误: {e}")

# 测试5: 错误的 Authorization 格式
print("\n5. 测试错误的 Authorization 格式")
print(f"GET {BASE_URL}/music/list")
headers = {"Authorization": TOKEN}  # 缺少 "Bearer " 前缀
try:
    r = requests.get(f"{BASE_URL}/music/list", headers=headers)
    print(f"  状态码: {r.status_code}")
    if r.status_code == 401:
        print(f"  ✅ 认证拒绝成功")
        try:
            print(f"  响应: {r.json()}")
        except:
            print(f"  响应文本: {r.text}")
    else:
        print(f"  响应: {r.json()}")
except Exception as e:
    print(f"  错误: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
print("\n使用说明:")
print("1. 修改 TOKEN 变量为你的 .env 中的 STATIC_TOKEN")
print("2. 所有 API 请求都需要在 Header 中添加:")
print("   Authorization: Bearer <your_token>")
print("3. 白名单路径不需要认证: /, /docs, /redoc, /openapi.json")
