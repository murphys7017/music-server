# 消息队列 + 定时任务系统使用文档 / Message Queue + Scheduler System Usage Guide

## 📦 系统概述 / System Overview

这是一个完整的轻量级任务调度系统,由 **消息队列** 和 **定时调度器** 两部分组成:

- **消息队列 (MemoryQueue)**: 线程安全的任务队列 + 公共信息存储
- **定时调度器 (Scheduler)**: 支持 interval/cron/once 三种调度方式,自动生成任务推入队列
- **数据库持久化**: 定时任务保存在数据库,系统重启后继续执行

### 核心特性 / Core Features

✅ **纯Python实现** - 仅使用标准库(queue, threading, time)  
✅ **零外部依赖** - 不依赖 Redis/RabbitMQ 等外部服务  
✅ **线程安全** - 所有操作都是线程安全的  
✅ **数据库持久化** - 定时任务保存在数据库  
✅ **灵活扩展** - 易于添加新任务类型和处理器  
✅ **完整日志** - 集成 loguru 日志系统  

---

## 📁 项目文件清单 / Project File List

### 核心模块文件 / Core Module Files (必需复制)

```
app/
├── core/
│   ├── __init__.py                    # 核心模块初始化
│   ├── message_queue.py               # ⭐ 消息队列核心 (320行)
│   │   ├── MemoryQueue 类
│   │   ├── 任务队列 (push_task, pop_task)
│   │   ├── 公共存储 (set_public, get_public)
│   │   ├── TTL过期清理
│   │   └── 全局单例 (get_queue)
│   │
│   └── scheduler.py                   # ⭐ 定时调度器 (540行)
│       ├── Scheduler 类
│       ├── 三种调度类型 (interval/cron/once)
│       ├── 任务管理 (add/pause/resume/delete)
│       ├── 数据库持久化
│       └── 全局单例 (get_scheduler)
│
├── models/
│   └── scheduler_task.py              # ⭐ 数据库模型 (100行)
│       ├── SchedulerTask - 定时任务表
│       └── TaskQueue - 任务队列表
│
├── log.py                             # 日志系统 (依赖 loguru)
├── database.py                        # 数据库连接 (依赖 SQLAlchemy)
└── config.py                          # 配置管理 (可选)
```

### 测试文件 / Test Files (可选)

```
test/
├── test_message_queue.py              # 消息队列测试 (200行)
└── test_scheduler.py                  # 调度器测试 (250行)
```

### 文档文件 / Documentation Files (推荐)

```
docs/
├── message_queue_usage.md             # 本文档
├── scheduler_usage.md                 # 调度器详细文档
└── README.md                          # 完整系统文档
```

---

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

### 运行方式 / Running Tests

**方法1: 直接运行 (推荐)**
```bash
python test/test_message_queue.py
python test/test_scheduler.py
```

**方法2: 从项目根目录**
```bash
cd C:\Users\Administrator\Downloads\song\music-server
python test/test_scheduler.py
```

**注意**: 测试文件已自动处理Python路径,可以直接运行。

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

---

## 📚 相关文档 / Related Documentation

- [定时调度器详细文档](./scheduler_usage.md) - Scheduler完整API和使用说明
- [完整系统文档](./README.md) - 整体系统架构和集成指南

---

## 🎁 快速复用模板 / Quick Reuse Template

### 最小复用文件清单 / Minimum Files Checklist

```
✅ app/core/message_queue.py       (消息队列核心,320行)
✅ app/core/scheduler.py           (定时调度器,540行)
✅ app/models/scheduler_task.py    (数据库模型,100行)
✅ app/database.py                 (数据库连接,50行)
✅ app/log.py                      (日志配置,30行)
---
总计: ~1040行代码
```

### 一键启动脚本 / One-Click Startup Script

创建 `start_queue_system.py`:

```python
"""
消息队列 + 定时任务系统 - 一键启动脚本
Quick Start Script for Message Queue + Scheduler System
"""

import threading
import time
from app.core.scheduler import get_scheduler
from app.core.message_queue import get_queue
from app.log import logger
from app.database import engine, Base

# ========== 1. 初始化数据库 ==========
def init_database():
    """创建数据库表"""
    logger.info("初始化数据库表...")
    Base.metadata.create_all(bind=engine)
    logger.success("数据库表创建完成")

# ========== 2. 定义任务处理器 ==========
TASK_HANDLERS = {
    "test_task": lambda params: logger.info(f"执行测试任务: {params}"),
    # 在这里添加你的任务处理器
}

def process_task(task):
    """统一任务处理入口"""
    task_type = task.get("type")
    params = task.get("params", {})
    
    handler = TASK_HANDLERS.get(task_type)
    if handler:
        handler(params)
    else:
        logger.warning(f"未知任务类型: {task_type}")

# ========== 3. Worker线程 ==========
def worker(worker_id):
    """Worker线程"""
    queue = get_queue()
    logger.info(f"Worker-{worker_id} 已启动")
    
    while True:
        task = queue.pop_task(timeout=5)
        if task:
            try:
                logger.info(f"[Worker-{worker_id}] 处理任务: {task.get('task_id')}")
                process_task(task)
                queue.task_done()
                logger.success(f"[Worker-{worker_id}] 任务完成")
            except Exception as e:
                logger.error(f"[Worker-{worker_id}] 任务失败: {e}")

# ========== 4. 主函数 ==========
def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("消息队列 + 定时任务系统启动中...")
    logger.info("=" * 60)
    
    # 初始化数据库
    init_database()
    
    # 启动调度器
    scheduler = get_scheduler()
    logger.success("定时调度器已启动")
    
    # 启动Worker线程
    worker_count = 3
    for i in range(worker_count):
        threading.Thread(target=worker, args=(i,), daemon=True).start()
    logger.success(f"已启动 {worker_count} 个Worker线程")
    
    # 示例: 添加测试任务
    logger.info("\n添加示例定时任务...")
    scheduler.add_scheduler_task(
        name="测试任务",
        task_type="test_task",
        schedule_type="interval",
        interval_seconds=10,
        params={"message": "Hello from scheduler!"},
        max_runs=5,
        description="每10秒执行一次,共5次"
    )
    
    logger.success("\n✅ 系统启动完成!")
    logger.info("📊 系统状态:")
    logger.info(f"  - 调度器: 运行中")
    logger.info(f"  - Worker数量: {worker_count}")
    logger.info(f"  - 队列大小: {get_queue().get_queue_size()}")
    logger.info("\n按 Ctrl+C 停止系统\n")
    
    # 保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n系统正在关闭...")
        logger.success("系统已停止")

if __name__ == "__main__":
    main()
```

**使用方法:**
```bash
python start_queue_system.py
```

---

## 💡 常见问题 / FAQ

### Q1: 如何在其他项目中使用?

**A:** 只需复制5个核心文件:
1. `app/core/message_queue.py` - 消息队列
2. `app/core/scheduler.py` - 调度器
3. `app/models/scheduler_task.py` - 数据库模型
4. `app/database.py` - 数据库连接(需修改连接字符串)
5. `app/log.py` - 日志配置

然后安装依赖: `pip install loguru sqlalchemy pymysql`

### Q2: 是否必须使用MySQL?

**A:** 不是。SQLAlchemy支持多种数据库:
- MySQL: `mysql+pymysql://...`
- PostgreSQL: `postgresql://...`
- SQLite: `sqlite:///./test.db`
- 修改 `database.py` 中的 `DATABASE_URL` 即可

### Q3: 任务会丢失吗?

**A:** 
- **内存队列中的任务**: 重启会丢失
- **定时任务**: 保存在数据库,重启后继续执行
- **可选**: 启用 `TaskQueue` 表持久化所有任务

### Q4: 如何监控任务执行?

**A:** 
```python
from app.core.message_queue import get_queue
from app.core.scheduler import get_scheduler

queue = get_queue()
scheduler = get_scheduler()

# 队列状态
print(f"队列大小: {queue.get_queue_size()}")
print(f"公共存储: {queue.get_store_size()}")

# 定时任务状态
tasks = scheduler.list_tasks(enabled_only=True)
for task in tasks:
    print(f"{task['name']}: 执行{task['run_count']}次")
```

### Q5: 可以替换为Redis吗?

**A:** 可以。实现一个 `RedisQueue` 类,保持相同的接口:
```python
class RedisQueue:
    def push_task(self, task): pass
    def pop_task(self, timeout): pass
    def set_public(self, key, value, ttl): pass
    def get_public(self, key): pass
```

### Q6: 如何处理任务失败?

**A:** 参考上面的"任务重试机制"示例,或:
```python
try:
    process_task(task)
except Exception as e:
    logger.error(f"任务失败: {e}")
    # 1. 记录到数据库
    # 2. 发送告警通知
    # 3. 推入死信队列
    # 4. 重试任务
```

---

## 📞 技术支持 / Technical Support

如果在复用过程中遇到问题:

1. 查看详细文档: `docs/README.md`
2. 运行测试: `python test_message_queue.py`
3. 检查日志: `logs/app_*.log`
4. 参考示例: `test_scheduler.py`

---

## 📄 License

MIT License - 自由使用和修改

## 📝 示例代码 / Example Code

查看 `test_message_queue.py` 获取完整示例。

---

## 🔄 与定时调度器集成 / Integration with Scheduler

### 完整系统架构 / Complete System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Scheduler (定时调度器)                   │  │
│  │  - 从数据库加载定时任务                               │  │
│  │  - 每10秒检查任务是否到期                             │  │
│  │  - 到期自动生成普通任务 ──┐                           │  │
│  └───────────────────────────┼───────────────────────────┘  │
│                               │                               │
│                               ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            MemoryQueue (消息队列)                     │  │
│  │  ┌──────────────────┐  ┌──────────────────┐         │  │
│  │  │  Task Queue      │  │  Public Store    │         │  │
│  │  │  任务队列         │  │  公共信息存储     │         │  │
│  │  │  (线程安全)       │  │  (支持TTL)       │         │  │
│  │  └──────────────────┘  └──────────────────┘         │  │
│  └───────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼─────────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │    Worker Threads (工作线程)  │
            │  - 从队列弹出任务              │
            │  - 执行业务逻辑                │
            │  - 标记任务完成                │
            └──────────────────────────────┘
```

### 使用定时调度器 / Using Scheduler

```python
from app.core.scheduler import get_scheduler
from app.core.message_queue import get_queue

# 1. 获取调度器实例 (自动启动)
scheduler = get_scheduler()

# 2. 添加定时任务 - 每30秒执行一次
task_id = scheduler.add_scheduler_task(
    name="定期下载B站音乐",
    task_type="download_bilibili_audio",
    schedule_type="interval",
    interval_seconds=30,
    params={
        "bv_id": "BV1xx411c7XZ",
        "quality": "320k"
    },
    max_runs=10,  # 最多执行10次
    description="每30秒下载一次,共执行10次"
)

# 3. 定时任务到期后会自动推入消息队列
# 4. Worker从队列消费任务并处理
```

### 完整示例 / Complete Example

```python
import threading
import time
from app.core.scheduler import get_scheduler
from app.core.message_queue import get_queue, set_public, get_public
from app.log import logger

# ========== 步骤1: 定义任务处理器 ==========
def process_download_audio(params):
    """处理音频下载任务"""
    url = params.get("url")
    save_path = params.get("save_path")
    logger.info(f"开始下载: {url} -> {save_path}")
    # 实际下载逻辑...
    time.sleep(2)
    logger.success("下载完成")

def process_convert_format(params):
    """处理格式转换任务"""
    input_file = params.get("input_file")
    output_format = params.get("output_format")
    logger.info(f"开始转换: {input_file} -> {output_format}")
    # 实际转换逻辑...
    time.sleep(1)
    logger.success("转换完成")

# 任务处理器注册表
TASK_HANDLERS = {
    "download_audio": process_download_audio,
    "convert_format": process_convert_format,
}

# ========== 步骤2: 创建Worker线程 ==========
def worker(worker_id):
    """Worker线程,处理队列中的任务"""
    queue = get_queue()
    logger.info(f"Worker-{worker_id} 已启动")
    
    while True:
        task = queue.pop_task(timeout=5)
        if task:
            task_id = task.get("task_id")
            task_type = task.get("type")
            params = task.get("params", {})
            
            logger.info(f"[Worker-{worker_id}] 处理任务: {task_id} [{task_type}]")
            
            # 调用对应的处理器
            handler = TASK_HANDLERS.get(task_type)
            if handler:
                try:
                    handler(params)
                    queue.task_done()
                    logger.success(f"[Worker-{worker_id}] 任务完成: {task_id}")
                except Exception as e:
                    logger.error(f"[Worker-{worker_id}] 任务失败: {e}")
            else:
                logger.warning(f"[Worker-{worker_id}] 未知任务类型: {task_type}")

# ========== 步骤3: 启动Worker ==========
# 启动3个Worker线程
for i in range(3):
    threading.Thread(target=worker, args=(i,), daemon=True).start()

# ========== 步骤4: 配置定时任务 ==========
scheduler = get_scheduler()

# 设置公共配置
set_public("bilibili_cookie", "SESSDATA=xxx", ttl=3600)

# 每小时下载一次收藏夹
scheduler.add_scheduler_task(
    name="每小时下载收藏夹",
    task_type="download_audio",
    schedule_type="interval",
    interval_seconds=3600,
    params={"url": "https://example.com/favorites"}
)

# 每天凌晨2点转换格式
scheduler.add_scheduler_task(
    name="每日格式转换",
    task_type="convert_format",
    schedule_type="cron",
    cron_expression="0 2 * * *",
    params={"input_file": "/music/temp", "output_format": "flac"}
)

# 5秒后执行一次
scheduler.add_scheduler_task(
    name="延迟下载",
    task_type="download_audio",
    schedule_type="once",
    execute_at=int(time.time()) + 5,
    params={"url": "https://example.com/song.mp3"}
)

logger.info("系统已启动,等待任务执行...")
```

---

## 🎯 项目复用指南 / Project Reuse Guide

### 复用步骤 / Reuse Steps

#### 1️⃣ 复制核心文件 (最小依赖)

```bash
# 创建目标项目结构
mkdir -p your_project/app/core
mkdir -p your_project/app/models

# 复制核心文件
cp app/core/message_queue.py your_project/app/core/
cp app/core/scheduler.py your_project/app/core/
cp app/models/scheduler_task.py your_project/app/models/
```

#### 2️⃣ 安装依赖

```bash
pip install loguru sqlalchemy pymysql
```

或添加到 `requirements.txt`:
```txt
loguru>=0.7.0
sqlalchemy>=2.0.0
pymysql>=1.1.0
```

#### 3️⃣ 配置数据库连接

创建 `app/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 修改为你的数据库连接
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/your_database"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 4️⃣ 配置日志系统

创建 `app/log.py`:
```python
from loguru import logger
import sys

# 配置日志格式
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

# 可选: 添加文件日志
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    level="DEBUG"
)
```

#### 5️⃣ 初始化数据库表

```python
from app.database import engine, Base
from app.models.scheduler_task import SchedulerTask, TaskQueue

# 创建表
Base.metadata.create_all(bind=engine)
```

#### 6️⃣ 在主应用中启动

```python
# main.py
from app.core.scheduler import get_scheduler
from app.core.message_queue import get_queue
from app.log import logger
import threading

# 启动调度器
scheduler = get_scheduler()
logger.info("调度器已启动")

# 启动Worker
def worker():
    queue = get_queue()
    while True:
        task = queue.pop_task(timeout=5)
        if task:
            # 处理任务
            process_task(task)
            queue.task_done()

# 启动多个Worker线程
for i in range(3):
    threading.Thread(target=worker, daemon=True).start()

# 你的应用逻辑...
if __name__ == "__main__":
    logger.info("应用已启动")
    # FastAPI/Flask/Django 或其他框架启动...
```

### 自定义扩展 / Custom Extensions

#### 扩展1: 添加新任务类型

```python
# 在你的项目中定义任务处理器
def process_send_email(params):
    to = params.get("to")
    subject = params.get("subject")
    content = params.get("content")
    # 发送邮件逻辑...
    send_email(to, subject, content)

# 注册到Worker
TASK_HANDLERS = {
    "send_email": process_send_email,
    "download_file": process_download_file,
    # 添加更多...
}

# 使用
from app.core.message_queue import push_task

push_task({
    "type": "send_email",
    "params": {
        "to": "user@example.com",
        "subject": "Hello",
        "content": "Test email"
    }
})
```

#### 扩展2: 添加任务优先级 (可选)

修改 `message_queue.py`:
```python
# 使用 PriorityQueue 替代 Queue
import queue

class MemoryQueue:
    def __init__(self):
        self._task_queue = queue.PriorityQueue()
        # ...
    
    def push_task(self, task: Dict[str, Any], priority: int = 0) -> str:
        # priority: 数字越小优先级越高
        self._task_queue.put((priority, task))
        # ...
```

#### 扩展3: 添加任务重试机制

```python
def worker_with_retry():
    queue = get_queue()
    
    while True:
        task = queue.pop_task(timeout=5)
        if task:
            retry_count = task.get("retry_count", 0)
            max_retries = task.get("max_retries", 3)
            
            try:
                process_task(task)
                queue.task_done()
            except Exception as e:
                logger.error(f"任务失败: {e}")
                
                if retry_count < max_retries:
                    # 重新推入队列
                    task["retry_count"] = retry_count + 1
                    queue.push_task(task)
                    logger.info(f"任务重试 {retry_count + 1}/{max_retries}")
                else:
                    logger.error(f"任务达到最大重试次数,放弃")
```

---

## 📋 依赖关系 / Dependencies

### 必需依赖 / Required

```python
# Python 标准库
import queue          # 线程安全队列
import threading      # 多线程支持
import time           # 时间管理
import uuid           # UUID生成
import json           # JSON序列化

# 第三方库
from loguru import logger           # 日志系统
from sqlalchemy import Column, ...  # ORM数据库
```

### 可选依赖 / Optional

```python
# 如果需要完整Cron支持
pip install croniter

# 使用croniter替代简化实现
from croniter import croniter

def _parse_cron_next_run(self, cron_expr: str, now: int) -> int:
    cron = croniter(cron_expr, now)
    return int(cron.get_next())
```

---

## 🔧 配置选项 / Configuration Options

### 消息队列配置

```python
from app.core.message_queue import MemoryQueue

# 自定义配置
queue = MemoryQueue(
    cleanup_interval=60  # 清理间隔(秒)
)
queue.start_cleanup()
```

### 调度器配置

```python
from app.core.scheduler import Scheduler

# 自定义配置
scheduler = Scheduler(
    check_interval=10  # 检查间隔(秒)
)
scheduler.start()
```

---

## 💾 数据库表结构 / Database Schema

### scheduler_task 表 (定时任务)

```sql
CREATE TABLE scheduler_task (
    task_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    params TEXT,
    schedule_type VARCHAR(20) NOT NULL,  -- interval/cron/once
    interval_seconds INT,
    cron_expression VARCHAR(100),
    execute_at BIGINT,
    last_run_at BIGINT,
    next_run_at BIGINT,
    run_count INT DEFAULT 0,
    max_runs INT DEFAULT 0,
    enabled BOOLEAN DEFAULT TRUE,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    description TEXT
);
```

### task_queue 表 (任务队列持久化,可选)

```sql
CREATE TABLE task_queue (
    task_id VARCHAR(36) PRIMARY KEY,
    task_type VARCHAR(100) NOT NULL,
    params TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority INT DEFAULT 0,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    created_at BIGINT NOT NULL,
    started_at BIGINT,
    completed_at BIGINT,
    error_message TEXT,
    scheduler_task_id VARCHAR(36)
);
```

---

## 🎯 最佳实践 / Best Practices

### 1. Worker数量配置

```python
import os

# 根据CPU核心数配置Worker
cpu_count = os.cpu_count() or 2
worker_count = min(cpu_count * 2, 10)  # 最多10个

for i in range(worker_count):
    threading.Thread(target=worker, args=(i,), daemon=True).start()
```

### 2. 任务超时控制

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("任务执行超时")

def worker_with_timeout():
    queue = get_queue()
    
    while True:
        task = queue.pop_task(timeout=5)
        if task:
            # 设置30秒超时
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            try:
                process_task(task)
                signal.alarm(0)  # 取消超时
                queue.task_done()
            except TimeoutError:
                logger.error("任务超时")
                signal.alarm(0)
```

### 3. 优雅关闭

```python
import signal
import sys

running = True

def signal_handler(sig, frame):
    global running
    logger.info("接收到关闭信号,等待任务完成...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def worker():
    queue = get_queue()
    while running:
        task = queue.pop_task(timeout=1)
        if task:
            process_task(task)
            queue.task_done()
    
    logger.info("Worker已停止")
```

---

## 🧪 测试命令 / Test Commands

```bash
# 测试消息队列
python test/test_message_queue.py

# 测试调度器
python test/test_scheduler.py

# 测试完整系统
python main.py
```
