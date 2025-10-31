# 消息队列使用文档 / Message Queue Usage Guide

## 📦 模块位置 / Module Location

```
app/core/message_queue.py
```

## 🚀 快速开始 / Quick Start

### 1. 基本导入 / Basic Import

```python
from app.core.message_queue import get_queue, push_task, pop_task, set_public, get_public
```

### 2. 推入任务 / Push Task

```python
# 自动生成任务ID
task_id = push_task({
    "type": "download_audio",
    "params": {
        "url": "https://example.com/song.mp3",
        "save_path": "/music/song.mp3"
    }
})

# 或者指定任务ID
task_id = push_task({
    "task_id": "my-custom-id",
    "type": "convert_format",
    "params": {"input": "song.mp3", "output": "song.flac"}
})
```

### 3. 处理任务 / Process Task

```python
import threading

def worker():
    queue = get_queue()
    while True:
        task = queue.pop_task(timeout=3)  # 超时3秒
        if task:
            print(f"Processing: {task['task_id']}")
            # 执行任务逻辑
            process_task(task)
            queue.task_done()

# 启动工作线程
threading.Thread(target=worker, daemon=True).start()
```

### 4. 公共信息存储 / Public Data Store

```python
# 设置永久数据
set_public("api_key", "your_api_key")

# 设置临时数据(60秒后过期)
set_public("session_token", "token123", ttl=60)

# 获取数据
api_key = get_public("api_key")

# 删除数据
delete_public("session_token")
```

## 📖 完整API / Full API

### MemoryQueue 类

#### 任务队列方法 / Task Queue Methods

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `push_task(task)` | 推入任务 | `task: Dict` | `task_id: str` |
| `pop_task(timeout)` | 弹出任务 | `timeout: float\|None` | `task: Dict\|None` |
| `task_done()` | 标记完成 | - | - |
| `get_queue_size()` | 队列大小 | - | `int` |
| `is_empty()` | 是否为空 | - | `bool` |

#### 公共存储方法 / Public Store Methods

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `set_public(key, value, ttl)` | 设置数据 | `key: str, value: Any, ttl: int\|None` | - |
| `get_public(key)` | 获取数据 | `key: str` | `Any\|None` |
| `delete_public(key)` | 删除数据 | `key: str` | `bool` |
| `cleanup()` | 清理过期 | - | - |
| `get_store_size()` | 存储大小 | - | `int` |
| `list_keys()` | 列出所有键 | - | `List[str]` |
| `clear_store()` | 清空存储 | - | - |

### 便捷函数 / Convenience Functions

```python
from app.core.message_queue import (
    push_task,      # 推入任务
    pop_task,       # 弹出任务
    set_public,     # 设置公共数据
    get_public,     # 获取公共数据
    delete_public   # 删除公共数据
)
```

## 🎯 使用场景 / Use Cases

### 场景1: B站音乐下载 / Bilibili Music Download

```python
from app.core.message_queue import push_task, set_public, get_public

# 设置B站cookie
set_public("bilibili_cookie", "SESSDATA=xxx; bili_jct=yyy", ttl=3600)

# 推入下载任务
task_id = push_task({
    "type": "download_bilibili_audio",
    "params": {
        "bv_id": "BV1xx411c7XZ",
        "quality": "320k",
        "save_path": "/music/downloads"
    }
})

# 存储任务状态
set_public(f"task_{task_id}_status", "pending")
```

### 场景2: 音频格式转换 / Audio Format Conversion

```python
# 批量转换任务
for file in audio_files:
    push_task({
        "type": "convert_format",
        "params": {
            "input_file": file,
            "output_format": "flac",
            "bitrate": "320k"
        }
    })
```

### 场景3: 多工作线程 / Multiple Workers

```python
import threading

def worker(worker_id):
    queue = get_queue()
    while True:
        task = queue.pop_task(timeout=5)
        if task:
            process_task(worker_id, task)
            queue.task_done()

# 启动3个工作线程
for i in range(3):
    threading.Thread(target=worker, args=(i,), daemon=True).start()
```

## ⚙️ 高级配置 / Advanced Configuration

### 自定义清理间隔

```python
from app.core.message_queue import MemoryQueue

# 创建自定义队列(每30秒清理一次)
queue = MemoryQueue(cleanup_interval=30)
queue.start_cleanup()
```

### 手动管理清理线程

```python
queue = get_queue()

# 停止自动清理
queue.stop_cleanup()

# 手动清理
queue.cleanup()

# 重新启动
queue.start_cleanup()
```

## 📊 监控和调试 / Monitoring & Debugging

```python
from app.core.message_queue import get_queue

queue = get_queue()

# 查看队列状态
print(f"队列大小: {queue.get_queue_size()}")
print(f"存储大小: {queue.get_store_size()}")
print(f"是否为空: {queue.is_empty()}")

# 查看所有公共数据键
print(f"所有键: {queue.list_keys()}")
```

## 🧪 运行测试 / Run Tests

```bash
python test_message_queue.py
```

测试包括:
- ✅ 基本队列功能
- ✅ 公共信息存储
- ✅ TTL过期测试
- ✅ 多工作线程
- ✅ B站下载场景模拟

## ⚠️ 注意事项 / Notes

1. **线程安全**: 所有操作都是线程安全的
2. **内存存储**: 数据存储在内存中,重启后丢失
3. **自动清理**: 后台线程会定期清理过期数据
4. **全局单例**: `get_queue()` 返回全局单例实例
5. **日志记录**: 所有操作都会记录到loguru日志系统

## 🔮 未来扩展 / Future Extensions

- [ ] 任务优先级队列
- [ ] 任务状态追踪系统
- [ ] 持久化到文件
- [ ] 任务回调机制
- [ ] 可替换后端(Redis/Database)
- [ ] 任务重试机制
- [ ] 任务超时控制

## 📝 示例代码 / Example Code

查看 `test_message_queue.py` 获取完整示例。
