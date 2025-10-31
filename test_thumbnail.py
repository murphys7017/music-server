"""
测试缩略图功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("测试音乐列表接口 (应包含 thumbnail_url，不包含 lyric)")
print("=" * 60)

try:
    r = requests.get(f"{BASE_URL}/music/list", params={"page": 1, "page_size": 2})
    data = r.json()
    
    print(f"状态码: {r.status_code}")
    print(f"响应:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if data.get("code") == 200:
        music_list = data.get("data", {}).get("list", [])
        if music_list:
            first_music = music_list[0]
            print("\n检查第一条音乐数据:")
            print(f"  ✓ 包含 thumbnail_url: {'thumbnail_url' in first_music}")
            print(f"  ✓ 包含 cover_url: {'cover_url' in first_music}")
            print(f"  ✓ 不包含 lyric: {'lyric' not in first_music}")
            
            if 'thumbnail_url' in first_music:
                print(f"\n  thumbnail_url: {first_music['thumbnail_url']}")
                
                # 测试缩略图接口
                if first_music['thumbnail_url']:
                    thumbnail_url = BASE_URL + first_music['thumbnail_url']
                    print(f"\n测试缩略图接口: {thumbnail_url}")
                    thumb_r = requests.get(thumbnail_url)
                    print(f"  状态码: {thumb_r.status_code}")
                    print(f"  Content-Type: {thumb_r.headers.get('content-type')}")
                    print(f"  文件大小: {len(thumb_r.content)} bytes")
                    
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 60)
print("测试音乐详情接口 (应包含 thumbnail_url 和 lyric)")
print("=" * 60)

try:
    # 先获取一个 UUID
    r = requests.get(f"{BASE_URL}/music/list", params={"page": 1, "page_size": 1})
    data = r.json()
    
    if data.get("code") == 200:
        music_list = data.get("data", {}).get("list", [])
        if music_list:
            uuid = music_list[0].get("uuid")
            print(f"使用 UUID: {uuid}")
            
            # 测试详情接口
            detail_r = requests.get(f"{BASE_URL}/music/detail/{uuid}")
            detail_data = detail_r.json()
            
            print(f"状态码: {detail_r.status_code}")
            print(f"响应:\n{json.dumps(detail_data, indent=2, ensure_ascii=False)}")
            
            if detail_data.get("code") == 200:
                music_detail = detail_data.get("data", {})
                print("\n检查详情数据:")
                print(f"  ✓ 包含 thumbnail_url: {'thumbnail_url' in music_detail}")
                print(f"  ✓ 包含 lyric: {'lyric' in music_detail}")
                
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n✅ 测试完成")
