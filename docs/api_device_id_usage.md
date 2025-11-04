# Device ID 使用指南

## 概述

`device_id` 用于标识客户端设备，支持以下接口的设备过滤和权限验证。

## 传递方式

### ✅ 推荐方式：请求头（Header）

```http
GET /music/list HTTP/1.1
Host: localhost:8000
Authorization: Bearer YOUR_TOKEN
X-Device-ID: client-uuid-12345
```

**优点：**
- 更符合 RESTful 规范
- 客户端统一配置，所有请求自动携带
- 避免 URL 参数污染
- 更安全（不会出现在日志 URL 中）

### 备选方式：查询参数（Query Parameter）

```http
GET /music/list?device_id=client-uuid-12345 HTTP/1.1
Host: localhost:8000
Authorization: Bearer YOUR_TOKEN
```

**适用场景：**
- 浏览器测试
- 临时查询不同设备的数据
- 向后兼容旧客户端

### 优先级规则

如果同时提供两种方式，**查询参数优先级更高**：

```
查询参数 device_id > 请求头 X-Device-ID
```

---

## API 接口

### 1. 查询音乐列表

**接口：** `GET /music/list`

**Device ID 用途：** 过滤设备音乐

```bash
# 方式1：请求头（推荐）
curl -X GET "http://localhost:8000/music/list?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Device-ID: client-uuid-12345"

# 方式2：查询参数
curl -X GET "http://localhost:8000/music/list?page=1&page_size=10&device_id=client-uuid-12345" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 查询所有音乐（不传 device_id）
curl -X GET "http://localhost:8000/music/list?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 仅查询服务端音乐
curl -X GET "http://localhost:8000/music/list?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Device-ID: server"
```

---

### 2. 搜索音乐

**接口：** `GET /music/search`

**Device ID 用途：** 在指定设备内搜索

```bash
# 方式1：请求头（推荐）
curl -X GET "http://localhost:8000/music/search?keyword=周杰伦&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Device-ID: client-uuid-12345"

# 方式2：查询参数
curl -X GET "http://localhost:8000/music/search?keyword=周杰伦&device_id=client-uuid-12345" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 搜索所有设备的音乐
curl -X GET "http://localhost:8000/music/search?keyword=周杰伦" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. 删除音乐

**接口：** `DELETE /music/{uuid}`

**Device ID 用途：** 权限验证（只能删除自己设备的音乐）

```bash
# 方式1：请求头（推荐）
curl -X DELETE "http://localhost:8000/music/abc-123-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Device-ID: client-uuid-12345"

# 方式2：查询参数
curl -X DELETE "http://localhost:8000/music/abc-123-uuid?device_id=client-uuid-12345" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 错误示例：缺少 device_id
curl -X DELETE "http://localhost:8000/music/abc-123-uuid" \
  -H "Authorization: Bearer YOUR_TOKEN"
# 返回: 400 Bad Request - "设备ID不能为空"
```

---

## 客户端实现示例

### Python (requests)

```python
import requests

class MusicClient:
    def __init__(self, base_url: str, token: str, device_id: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "X-Device-ID": device_id  # 统一配置
        }
    
    def list_music(self, page: int = 1, page_size: int = 10):
        """查询音乐列表"""
        response = requests.get(
            f"{self.base_url}/music/list",
            params={"page": page, "page_size": page_size},
            headers=self.headers  # 自动携带 device_id
        )
        return response.json()
    
    def search_music(self, keyword: str):
        """搜索音乐"""
        response = requests.get(
            f"{self.base_url}/music/search",
            params={"keyword": keyword},
            headers=self.headers
        )
        return response.json()
    
    def delete_music(self, uuid: str):
        """删除音乐"""
        response = requests.delete(
            f"{self.base_url}/music/{uuid}",
            headers=self.headers
        )
        return response.json()

# 使用
client = MusicClient(
    base_url="http://localhost:8000",
    token="YOUR_TOKEN",
    device_id="client-uuid-12345"
)

# 所有请求自动携带 device_id
music_list = client.list_music()
search_result = client.search_music("周杰伦")
client.delete_music("abc-123-uuid")
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

class MusicClient {
  constructor(baseURL, token, deviceId) {
    this.client = axios.create({
      baseURL: baseURL,
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Device-ID': deviceId  // 统一配置
      }
    });
  }
  
  async listMusic(page = 1, pageSize = 10) {
    const response = await this.client.get('/music/list', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  }
  
  async searchMusic(keyword) {
    const response = await this.client.get('/music/search', {
      params: { keyword }
    });
    return response.data;
  }
  
  async deleteMusic(uuid) {
    const response = await this.client.delete(`/music/${uuid}`);
    return response.data;
  }
}

// 使用
const client = new MusicClient(
  'http://localhost:8000',
  'YOUR_TOKEN',
  'client-uuid-12345'
);

// 所有请求自动携带 device_id
const musicList = await client.listMusic();
const searchResult = await client.searchMusic('周杰伦');
await client.deleteMusic('abc-123-uuid');
```

---

## 最佳实践

### ✅ 推荐做法

1. **客户端启动时生成/加载 device_id**
   ```python
   import uuid
   import json
   from pathlib import Path
   
   def get_or_create_device_id():
       config_file = Path("config.json")
       if config_file.exists():
           config = json.loads(config_file.read_text())
           return config["device_id"]
       
       device_id = str(uuid.uuid4())
       config_file.write_text(json.dumps({"device_id": device_id}))
       return device_id
   ```

2. **使用请求头统一传递**
   - 在 HTTP 客户端初始化时配置
   - 所有请求自动携带
   - 无需每次手动传递

3. **服务端音乐使用固定 device_id**
   - 使用 `"server"` 作为服务端音乐的 device_id
   - 便于区分和过滤

### ❌ 不推荐做法

1. **每次请求都手动传递查询参数**
   ```python
   # 不推荐：重复代码
   requests.get(f"{url}/music/list?device_id={device_id}")
   requests.get(f"{url}/music/search?keyword=x&device_id={device_id}")
   ```

2. **硬编码 device_id**
   ```python
   # 不推荐：所有客户端使用相同ID
   device_id = "my-client"
   ```

3. **每次生成新的 device_id**
   ```python
   # 不推荐：无法识别同一设备
   device_id = str(uuid.uuid4())  # 每次都不同
   ```

---

## 常见问题

### Q: 为什么 DELETE 接口必须提供 device_id？

**A:** 出于安全考虑，防止误删其他设备的音乐。客户端只能删除自己设备的音乐。

### Q: 如何查询所有设备的音乐？

**A:** 不传递 `device_id` 参数和请求头即可。

### Q: 可以更换 device_id 吗？

**A:** 可以，但会导致：
- 旧的音乐记录无法通过新 device_id 管理
- 建议将旧 device_id 的音乐迁移到新 device_id

### Q: 服务端如何添加音乐？

**A:** 使用 `music_scanner.py` 工具，会自动设置 `device_id="server"`。

---

## 向后兼容性

现有客户端无需立即修改：
- 查询参数方式仍然有效
- 但建议逐步迁移到请求头方式

迁移步骤：
1. 客户端添加 `X-Device-ID` 请求头
2. 测试验证功能正常
3. 移除查询参数中的 `device_id`
