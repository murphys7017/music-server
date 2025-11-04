# 客户端实现指南

本文档为客户端开发者提供完整的实现指南，帮助你快速集成音乐服务器。

---

## 📋 目录

- [系统架构](#系统架构)
- [本地数据库设计](#本地数据库设计)
- [初始化流程](#初始化流程)
- [音乐添加流程](#音乐添加流程)
- [资源获取策略](#资源获取策略)
- [API 调用示例](#api-调用示例)
- [常见问题](#常见问题)

---

## 🏗️ 系统架构

### 客户端-服务器交互模型

```
┌──────────────────────────────────────────┐
│           客户端应用                      │
│  ┌────────────────────────────────────┐  │
│  │  本地数据库 (SQLite)                │  │
│  │  - UUID → 文件路径映射              │  │
│  │  - 缓存信息                         │  │
│  └────────────┬───────────────────────┘  │
│               │                           │
│  ┌────────────▼───────────────────────┐  │
│  │  资源管理器                         │  │
│  │  - 优先本地                         │  │
│  │  - 降级服务器                       │  │
│  └────────────┬───────────────────────┘  │
└───────────────┼──────────────────────────┘
                │ HTTPS
                ▼
┌──────────────────────────────────────────┐
│        Music Server (服务器)             │
│  - 存储元数据                            │
│  - 提供设备管理                          │
│  - 不存储文件路径                        │
└──────────────────────────────────────────┘
```

### 核心原则

1. **隐私保护**: 文件路径不上传，只传元数据
2. **本地优先**: 资源优先从本地获取
3. **设备隔离**: 不同设备的音乐互不可见
4. **服务器共享**: `device_id="server"` 的音乐全局可见

---

## 💾 本地数据库设计

### SQLite 表结构

```sql
-- 资源映射表
CREATE TABLE resource_map (
    uuid TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL,  -- 'music', 'cover', 'lyric'
    local_path TEXT NOT NULL,
    file_hash TEXT,               -- MD5 hash
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP
);

-- 设备信息表（缓存）
CREATE TABLE device_info (
    device_id TEXT PRIMARY KEY,
    device_name TEXT NOT NULL,
    device_type TEXT,
    platform TEXT,
    app_version TEXT,
    synced_at TIMESTAMP
);

-- 索引
CREATE INDEX idx_resource_type ON resource_map(resource_type);
CREATE INDEX idx_local_path ON resource_map(local_path);
```

### Python 实现示例

```python
import sqlite3
import os
from pathlib import Path

class LocalDatabase:
    def __init__(self, db_path="music_client.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
        """创建表"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resource_map (
                uuid TEXT PRIMARY KEY,
                resource_type TEXT NOT NULL,
                local_path TEXT NOT NULL,
                file_hash TEXT,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_resource_type 
            ON resource_map(resource_type)
        ''')
        
        self.conn.commit()
    
    def add_mapping(self, uuid, resource_type, local_path, file_hash=None):
        """添加映射"""
        cursor = self.conn.cursor()
        file_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
        
        cursor.execute('''
            INSERT OR REPLACE INTO resource_map 
            (uuid, resource_type, local_path, file_hash, file_size)
            VALUES (?, ?, ?, ?, ?)
        ''', (uuid, resource_type, local_path, file_hash, file_size))
        
        self.conn.commit()
    
    def get_local_path(self, uuid):
        """获取本地路径"""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT local_path FROM resource_map WHERE uuid = ?',
            (uuid,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    
    def resource_exists_locally(self, uuid):
        """检查资源是否存在于本地"""
        local_path = self.get_local_path(uuid)
        return local_path and os.path.exists(local_path)
```

---

## 🚀 初始化流程

### 1. 生成设备 UUID

```python
import uuid
import platform

def get_device_id():
    """
    获取或生成设备ID
    首次运行时生成，后续从配置文件读取
    """
    config_file = "device_config.json"
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config['device_id']
    
    # 首次运行，生成新ID
    device_id = str(uuid.uuid4())
    
    config = {
        'device_id': device_id,
        'device_name': platform.node(),  # 计算机名
        'device_type': get_device_type(),
        'platform': platform.system(),
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    return device_id

def get_device_type():
    """判断设备类型"""
    system = platform.system()
    if system in ['Windows', 'Darwin', 'Linux']:
        return 'desktop'
    elif system in ['Android', 'iOS']:
        return 'mobile'
    return 'other'
```

### 2. 初始化 HTTP 客户端（配置 X-Device-ID）

```python
import requests

def init_http_client(device_id: str) -> requests.Session:
    """
    初始化 HTTP 客户端，统一配置 X-Device-ID 请求头
    推荐方式：在 Session 中配置全局请求头
    """
    session = requests.Session()
    session.headers.update({
        "X-Device-ID": device_id,  # 统一配置设备ID
        "Content-Type": "application/json",
        # 如需认证，添加 Authorization
        # "Authorization": f"Bearer {token}",
    })
    return session

# JavaScript/TypeScript 示例
# const axios = require('axios');
# 
# function initHttpClient(deviceId) {
#   return axios.create({
#     baseURL: 'http://your-server.com',
#     headers: {
#       'X-Device-ID': deviceId,
#       'Content-Type': 'application/json'
#     }
#   });
# }
```

### 3. 注册设备到服务器

```python
import requests

def register_device(server_url, token, device_info):
    """注册设备"""
    response = requests.post(
        f"{server_url}/device/register",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "device_id": device_info['device_id'],
            "device_name": device_info['device_name'],
            "device_type": device_info['device_type'],
            "platform": device_info['platform'],
            "app_version": "1.0.0"
        }
    )
    
    if response.status_code == 200:
        print("设备注册成功")
        return response.json()
    else:
        print(f"设备注册失败: {response.text}")
        return None
```

---

## 🎵 音乐添加流程

### 完整流程

```python
import hashlib
from mutagen import File as MutagenFile

def add_local_music(file_path, db, server_url, token, device_id):
    """
    添加本地音乐完整流程
    
    1. 提取元数据
    2. 计算 MD5
    3. 生成 UUID
    4. 保存本地映射
    5. 上传元数据到服务器
    """
    
    # 1. 提取元数据
    audio = MutagenFile(file_path)
    if not audio:
        raise ValueError("无法解析音频文件")
    
    metadata = extract_metadata(audio, file_path)
    
    # 2. 计算 MD5
    md5_hash = calculate_md5(file_path)
    
    # 3. 生成 UUID
    music_uuid = str(uuid.uuid4())
    
    # 4. 保存本地映射
    db.add_mapping(music_uuid, "music", file_path, md5_hash)
    
    # 5. 准备上传数据
    music_data = {
        "uuid": music_uuid,
        "md5": md5_hash,
        "device_id": device_id,
        "name": metadata['name'],
        "author": metadata['author'],
        "album": metadata['album'],
        "duration": metadata['duration'],
        "size": metadata['size'],
        "bitrate": metadata['bitrate'],
        "file_format": metadata['file_format'],
    }
    
    # 6. 上传到服务器（推荐：使用 Session 配置全局请求头）
    session = init_http_client(device_id)  # X-Device-ID 已配置
    response = session.post(
        f"{server_url}/music/add",
        json=music_data
    )
    
    # 备选方式：使用查询参数（不推荐但仍支持）
    # response = requests.post(
    #     f"{server_url}/music/add?device_id={device_id}",
    #     headers={"Authorization": f"Bearer {token}"},
    #     json=music_data
    # )
    
    if response.status_code == 200:
        print(f"音乐添加成功: {metadata['name']}")
        return music_uuid
    else:
        # 回滚本地映射
        db.delete_mapping(music_uuid)
        raise Exception(f"服务器添加失败: {response.text}")


def extract_metadata(audio, file_path):
    """提取音频元数据"""
    return {
        "name": audio.get("title", [os.path.basename(file_path)])[0],
        "author": audio.get("artist", ["未知"])[0],
        "album": audio.get("album", [""])[0],
        "duration": int(audio.info.length),
        "size": os.path.getsize(file_path),
        "bitrate": audio.info.bitrate // 1000,
        "file_format": os.path.splitext(file_path)[1][1:].lower(),
    }


def calculate_md5(file_path, chunk_size=8192):
    """计算文件 MD5"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            md5.update(chunk)
    return md5.hexdigest()
```

---

## 📦 资源获取策略

### 优先级逻辑

```python
class ResourceManager:
    def __init__(self, local_db, server_url, token):
        self.db = local_db
        self.server_url = server_url
        self.token = token
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_music_file(self, uuid):
        """
        获取音乐文件
        优先级: 本地 > 服务器
        """
        # 1. 检查本地映射
        local_path = self.db.get_local_path(uuid)
        if local_path and os.path.exists(local_path):
            print(f"从本地获取: {local_path}")
            return local_path
        
        # 2. 尝试从服务器下载（如果是 server 设备的音乐）
        print(f"UUID {uuid} 在本地不存在")
        return None
    
    def get_cover(self, cover_uuid):
        """
        获取封面
        优先级: 本地 > 缓存 > 服务器
        """
        # 1. 本地映射
        local_path = self.db.get_local_path(cover_uuid)
        if local_path and os.path.exists(local_path):
            return local_path
        
        # 2. 缓存
        cache_path = self.cache_dir / f"{cover_uuid}.jpg"
        if cache_path.exists():
            return str(cache_path)
        
        # 3. 从服务器下载
        try:
            response = requests.get(
                f"{self.server_url}/music/cover/{cover_uuid}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                return str(cache_path)
        except Exception as e:
            print(f"下载封面失败: {e}")
        
        return None
    
    def get_thumbnail(self, cover_uuid):
        """获取缩略图（用于列表显示）"""
        cache_path = self.cache_dir / f"{cover_uuid}_thumb.jpg"
        
        if cache_path.exists():
            return str(cache_path)
        
        try:
            response = requests.get(
                f"{self.server_url}/music/thumbnail/{cover_uuid}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                return str(cache_path)
        except Exception as e:
            print(f"下载缩略图失败: {e}")
        
        return None
```

---

## 🌐 API 调用示例

> **推荐方式**: 使用 `X-Device-ID` 请求头传递设备ID，更符合 RESTful 规范。
> 详细说明请参考：[API Device ID 使用指南](./api_device_id_usage.md)

### 1. 获取音乐列表

```python
def get_music_list(session, server_url, page=1, page_size=20):
    """
    获取音乐列表（使用请求头）
    
    Args:
        session: 已配置 X-Device-ID 的 requests.Session
        page: 页码
        page_size: 每页数量
    """
    response = session.get(
        f"{server_url}/music/list",
        params={
            "page": page,
            "page_size": page_size
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        return data['data']['list']
    else:
        raise Exception(f"获取列表失败: {response.text}")

# 兼容旧方式：使用查询参数（不推荐）
def get_music_list_legacy(server_url, token, device_id, page=1, page_size=20):
    """使用查询参数方式（向后兼容）"""
    response = requests.get(
        f"{server_url}/music/list",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "device_id": device_id,  # 查询参数优先级高于请求头
            "page": page,
            "page_size": page_size
        }
    )
    return response.json()['data']['list']
```

### 2. 搜索音乐

```python
def search_music(session, server_url, keyword, page=1, page_size=50):
    """搜索音乐（使用请求头）"""
    response = session.get(
        f"{server_url}/music/search",
        params={
            "keyword": keyword,
            "page": page,
            "page_size": page_size
        }
    )
    
    if response.status_code == 200:
        return response.json()['data']['list']
    else:
        raise Exception(f"搜索失败: {response.text}")
```

### 3. 删除音乐

```python
def delete_music(session, server_url, uuid):
    """删除音乐（使用请求头）"""
    response = session.delete(f"{server_url}/music/{uuid}")
    
    if response.status_code == 200:
        print(f"删除成功: {uuid}")
        return True
    else:
        print(f"删除失败: {response.text}")
        return False
```

### JavaScript 示例

```javascript
// 初始化 Axios 客户端
const axios = require('axios');

const apiClient = axios.create({
  baseURL: 'http://your-server.com',
  headers: {
    'X-Device-ID': deviceId,  // 统一配置
    'Content-Type': 'application/json'
  }
});

// 获取音乐列表
async function getMusicList(page = 1, pageSize = 20) {
  const response = await apiClient.get('/music/list', {
    params: { page, page_size: pageSize }
  });
  return response.data.data.list;
}

// 搜索音乐
async function searchMusic(keyword) {
  const response = await apiClient.get('/music/search', {
    params: { keyword, page: 1, page_size: 50 }
  });
  return response.data.data.list;
}

// 删除音乐
async function deleteMusic(uuid) {
  await apiClient.delete(`/music/${uuid}`);
  console.log(`删除成功: ${uuid}`);
}
```

---

## 🔄 请求头 vs 查询参数对比

| 方式 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **X-Device-ID 请求头** | ✅ 符合 RESTful 规范<br>✅ 统一配置一次<br>✅ URL 更简洁 | ⚠️ 需要客户端升级 | ⭐⭐⭐⭐⭐ |
| **查询参数** | ✅ 向后兼容<br>✅ 易于调试 | ❌ URL 冗长<br>❌ 每次都要传递 | ⭐⭐⭐ |

### 优先级规则

当同时提供查询参数和请求头时，**查询参数优先级更高**，用于显式覆盖默认设备ID。

```python
# 场景：临时查询其他设备的音乐
session = init_http_client("device-A")  # 默认设备A

# 查询设备B的音乐（查询参数覆盖）
response = session.get(
    f"{server_url}/music/list",
    params={"device_id": "device-B"}  # 显式覆盖
)
```

---

## ❓ 常见问题

### Q1: 封面和歌词如何关联？

**A**:
    
    return response.json()['data']['list']
```

### 3. 删除音乐

```python
def delete_music(server_url, token, uuid, device_id, local_db):
    """
    删除音乐
    
    1. 删除本地文件
    2. 删除本地映射
    3. 删除服务器记录
    """
    # 1. 获取本地路径
    local_path = local_db.get_local_path(uuid)
    
    # 2. 删除服务器记录
    response = requests.delete(
        f"{server_url}/music/{uuid}",
        headers={"Authorization": f"Bearer {token}"},
        params={"device_id": device_id}
    )
    
    if response.status_code != 200:
        raise Exception(f"服务器删除失败: {response.text}")
    
    # 3. 删除本地文件
    if local_path and os.path.exists(local_path):
        os.remove(local_path)
        print(f"本地文件已删除: {local_path}")
    
    # 4. 删除本地映射
    local_db.delete_mapping(uuid)
    
    print(f"音乐删除成功: {uuid}")
```

---

## ❓ 常见问题

### Q1: 如何处理同一文件在多个设备？

**A**: 每个设备分别添加，服务器通过 `(md5, device_id)` 联合唯一索引区分。不同设备的相同文件会有不同的 UUID。

### Q2: 封面和歌词如何同步？

**A**: 
- 客户端添加音乐时，如果有封面/歌词，同时保存本地映射
- 服务器只存储 `cover_uuid` 和 `lyric` 文本
- 其他设备从服务器下载后缓存

### Q3: 如何实现离线播放？

**A**:
- 本地音乐：直接播放，无需网络
- 服务器音乐：首次播放时下载并缓存
- 缓存策略：LRU（最近最少使用）

### Q4: 设备切换如何保持音乐库？

**A**:
- 每个设备独立音乐库
- 服务器音乐（device_id="server"）全局可见
- 可以在设置中"查看所有设备的音乐"

### Q5: MD5 冲突怎么办？

**A**:
- 同一设备：`(md5, device_id)` 唯一，拒绝重复添加
- 不同设备：允许相同 MD5，不同 UUID

---

## 📊 性能建议

1. **批量操作**: 添加多首音乐时，先本地处理，再批量上传
2. **缩略图**: 列表使用缩略图（~20KB），详情页加载原图
3. **懒加载**: 音乐列表分页加载，封面异步加载
4. **缓存策略**: 封面/缩略图永久缓存，音乐文件按 LRU
5. **数据库索引**: 本地数据库对 uuid 和 resource_type 建索引

---

## 🔒 安全建议

1. **Token 存储**: 使用系统 Keychain/Keystore 存储
2. **HTTPS**: 生产环境必须使用 HTTPS
3. **文件权限**: 音乐文件设置合适的读写权限
4. **数据库加密**: 敏感数据考虑使用 SQLCipher

---

## 📱 平台特定建议

### iOS
- 使用 Core Data 或 SQLite.swift
- 封面缓存使用 FileManager
- 后台下载使用 URLSession

### Android
- 使用 Room 数据库
- 封面缓存使用 Glide/Coil
- MediaStore 集成

### Desktop (Electron/Qt)
- SQLite3 数据库
- 本地文件管理
- 系统托盘集成

---

## 🎯 总结

客户端实现的核心要点：

1. ✅ 本地数据库维护 UUID → 文件路径映射
2. ✅ 优先使用本地资源，降级到服务器
3. ✅ 文件路径永不上传，保护隐私
4. ✅ 设备隔离，各自管理音乐库
5. ✅ 服务器音乐全局共享

完整示例代码请参考: [客户端示例项目](https://github.com/your-repo/music-client-example)
