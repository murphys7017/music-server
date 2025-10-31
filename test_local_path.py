"""
测试服务端本地路径功能
使用方法：
1. 启动服务器: python main.py
2. 运行此脚本: python test_local_path.py
"""
import requests
import uuid

BASE_URL = "http://localhost:8000"
TOKEN = "EjSYN_2hc2wcYvEsprgd5oEdnliiWtJ8ueGwEETZMlY"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

def test_add_server_music():
    """测试添加服务端音乐（带local_path）"""
    music_uuid = str(uuid.uuid4())
    
    data = {
        "uuid": music_uuid,
        "md5": "test_server_md5_001",
        "device_id": "server",  # 服务端音乐
        "name": "服务端测试歌曲",
        "author": "测试歌手",
        "album": "测试专辑",
        "local_path": "D:/Music/test_song.mp3",  # 本地文件路径
        "duration": 180,
        "size": 5242880,
        "bitrate": 320,
        "file_format": "mp3"
    }
    
    response = requests.post(
        f"{BASE_URL}/music/add",
        json=data,
        headers=headers
    )
    
    print("添加服务端音乐:")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()
    
    return music_uuid


def test_query_music(device_id=None):
    """查询音乐列表"""
    params = {"page": 1, "page_size": 10}
    if device_id:
        params["device_id"] = device_id
    
    response = requests.get(
        f"{BASE_URL}/music/list",
        params=params,
        headers=headers
    )
    
    print(f"查询音乐列表 (device_id={device_id}):")
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"总数: {result['data']['total']}")
    
    for music in result['data']['list']:
        print(f"  - {music['name']} ({music['author']})")
        print(f"    UUID: {music['uuid']}")
        print(f"    Device: {music['device_id']}")
        print(f"    Local Path: {music.get('local_path', 'N/A')}")
    print()


def test_get_music_detail(music_uuid):
    """查询音乐详情"""
    response = requests.get(
        f"{BASE_URL}/music/{music_uuid}",
        headers=headers
    )
    
    print(f"查询音乐详情 ({music_uuid}):")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        music = response.json()['data']
        print(f"  名称: {music['name']}")
        print(f"  作者: {music['author']}")
        print(f"  设备: {music['device_id']}")
        print(f"  本地路径: {music.get('local_path', 'N/A')}")
        print(f"  格式: {music.get('file_format', 'N/A')}")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("测试服务端本地路径功能")
    print("=" * 50)
    print()
    
    # 1. 添加服务端音乐
    music_uuid = test_add_server_music()
    
    # 2. 查询所有音乐
    test_query_music()
    
    # 3. 查询服务端音乐
    test_query_music(device_id="server")
    
    # 4. 查询音乐详情
    test_get_music_detail(music_uuid)
    
    print("=" * 50)
    print("测试完成！")
    print("=" * 50)
