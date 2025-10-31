# Music Server 音乐服务器完整文档

## 📖 目录 / Table of Contents

- [项目概述](#项目概述)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [核心功能](#核心功能)
- [API文档](#api文档)
- [开发指南](#开发指南)

---

## 🎯 项目概述 / Project Overview

这是一个功能完整的音乐服务器系统,支持:
- 🎵 音乐管理(数据库存储、元数据提取)
- 📁 文件扫描(自动扫描文件夹导入音乐)
- 🎨 封面管理(内嵌封面提取、外部封面关联)
- 📝 歌词管理(内嵌歌词、外部lrc文件)
- 🔄 消息队列(轻量级任务队列系统)
- ⏰ 定时任务(支持interval/cron/once调度)
- 🎬 B站集成(计划支持B站音乐下载)

### 技术栈 / Tech Stack

- **Web框架**: FastAPI
- **数据库**: MySQL + SQLAlchemy ORM
- **音频处理**: Mutagen (元数据提取)
- **日志系统**: Loguru
- **消息队列**: 内存队列(Python queue + threading)
- **调度器**: 自研定时任务系统

---

## 🏗️ 系统架构 / System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Music Router │  │ 其他路由...   │  │  Scheduler   │      │
│  └──────┬───────┘  └──────────────┘  └──────┬───────┘      │
│         │                                     │               │
│  ┌──────▼───────────────────────────────────▼───────┐      │
│  │           Message Queue (消息队列)                │      │
│  │  - Task Queue (任务队列)                          │      │
│  │  - Public Store (公共信息存储)                    │      │
│  └──────┬───────────────────────────────────────────┘      │
└─────────┼─────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Worker Threads (工作线程)                 │
│  - 处理下载任务                                               │
│  - 处理转换任务                                               │
│  - 处理扫描任务                                               │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer (数据层)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Music   │  │SchedulerTask│ TaskQueue│  │  其他...  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始 / Quick Start

### 1. 安装依赖

```bash
pip install fastapi uvicorn sqlalchemy pymysql mutagen loguru
```

或使用 uv:
```bash
uv pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或设置环境变量:

```bash
# 音乐目录
MUSIC_DIR=C:\Users\Administrator\Downloads\song\test
# 封面目录
COVER_DIR=C:\Users\Administrator\Downloads\song\covers
# MySQL连接
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=music_server
```

### 3. 初始化数据库

```python
from app.database import engine, Base

# 创建所有表
Base.metadata.create_all(bind=engine)
```

### 4. 启动服务器

```bash
python main.py
```

或
```bash
uvicorn main:app --reload
```

服务器将在 `http://localhost:8000` 启动。

### 5. 访问API文档

打开浏览器访问:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🎯 核心功能 / Core Features

### 1. 音乐管理 📁

#### 扫描音乐文件夹

```python
from app.utils.music_scanner import scan_and_import_folder

# 扫描文件夹并导入到数据库
scan_and_import_folder(
    folder_path="/path/to/music",
    skip_existing=True,      # 跳过已存在的文件
    upgrade_quality=True     # 如果有更高质量版本,升级
)
```

**功能特性:**
- ✅ 自动提取音频元数据(标题、艺术家、专辑、时长、比特率)
- ✅ 提取内嵌封面(ID3/FLAC)
- ✅ 提取内嵌歌词
- ✅ 查找外部封面文件(同名.jpg/.png)
- ✅ 查找外部歌词文件(同名.lrc)
- ✅ MD5去重(避免重复导入)
- ✅ 质量升级(保留高质量版本,合并信息)

#### 文件名解析

```python
from app.utils.music_filename_parser import parse_filename

info = parse_filename("玉盘 - 葫芦童声.flac")
# 返回: {"name": "玉盘", "author": "葫芦童声", ...}
```

支持格式:
- `歌曲名 - 艺术家`
- `歌曲名 (类型) - 艺术家`
- `艺术家1 _ 艺术家2 - 歌曲名`
- 自动识别伴奏、Remix、Instrumental等版本

### 2. 消息队列系统 📬

详细文档: [message_queue_usage.md](./message_queue_usage.md)

```python
from app.core.message_queue import push_task, pop_task, set_public, get_public

# 推入任务
task_id = push_task({
    "type": "download_audio",
    "params": {"url": "...", "save_path": "..."}
})

# 设置公共信息(支持TTL)
set_public("bilibili_cookie", "SESSDATA=xxx", ttl=3600)

# 获取公共信息
cookie = get_public("bilibili_cookie")

# Worker处理任务
def worker():
    while True:
        task = pop_task(timeout=3)
        if task:
            process(task)
```

**功能特性:**
- ✅ 线程安全的任务队列
- ✅ 公共信息存储(带TTL)
- ✅ 自动过期清理
- ✅ 多Worker支持

### 3. 定时任务调度器 ⏰

详细文档: [scheduler_usage.md](./scheduler_usage.md)

```python
from app.core.scheduler import get_scheduler

scheduler = get_scheduler()

# 间隔调度 - 每30秒执行
scheduler.add_scheduler_task(
    name="定期下载音乐",
    task_type="download_audio",
    schedule_type="interval",
    interval_seconds=30,
    max_runs=10,
    params={"url": "..."}
)

# 单次执行 - 5秒后执行
import time
scheduler.add_scheduler_task(
    name="延迟任务",
    task_type="convert_audio",
    schedule_type="once",
    execute_at=int(time.time()) + 5,
    params={"input": "song.mp3"}
)

# Cron调度 - 每小时整点执行
scheduler.add_scheduler_task(
    name="清理任务",
    task_type="cleanup",
    schedule_type="cron",
    cron_expression="0 * * * *",
    params={"dir": "/tmp"}
)
```

**功能特性:**
- ✅ 三种调度类型(interval/cron/once)
- ✅ 数据库持久化(重启后继续执行)
- ✅ 动态管理(添加/暂停/恢复/删除)
- ✅ 最大执行次数限制
- ✅ 自动推入消息队列

---

## 🔌 API文档 / API Documentation

### 音乐相关 API

#### 1. 列出音乐 (分页)
```http
GET /music/list?page=1&page_size=20
```

**响应:**
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
      "name": "玉盘",
      "author": "葫芦童声",
      "album": "专辑名",
      "duration": 245,
      "size": 10485760,
      "bitrate": 320,
      "cover_uuid": "cover-uuid",
      "play_count": 10,
      "play_url": "/music/play/{uuid}",
      "cover_url": "/music/cover/{cover_uuid}"
    }
  ]
}
```

#### 2. 搜索音乐
```http
GET /music/search?keyword=玉盘&page=1&page_size=20
```

#### 3. 获取音乐详情
```http
GET /music/{music_uuid}
```

#### 4. 播放音乐
```http
GET /music/play/{music_uuid}
```
返回音频流,自动增加播放次数

#### 5. 获取封面
```http
GET /music/cover/{cover_uuid}
```

#### 6. 获取歌词
```http
GET /music/lyric/{music_uuid}
```

---

## 🛠️ 开发指南 / Development Guide

### 项目结构

```
music-server/
├── app/
│   ├── core/                    # 核心模块
│   │   ├── __init__.py
│   │   ├── message_queue.py    # 消息队列
│   │   └── scheduler.py        # 定时任务调度器
│   ├── models/                  # 数据库模型
│   │   ├── __init__.py
│   │   ├── music.py            # 音乐模型
│   │   └── scheduler_task.py   # 调度任务模型
│   ├── routers/                 # API路由
│   │   ├── __init__.py
│   │   └── music.py            # 音乐路由
│   ├── services/                # 业务逻辑
│   │   ├── __init__.py
│   │   └── music_service.py    # 音乐服务
│   ├── utils/                   # 工具函数
│   │   ├── __init__.py
│   │   ├── music_filename_parser.py  # 文件名解析
│   │   └── music_scanner.py          # 音乐扫描
│   ├── config.py                # 配置管理
│   ├── database.py              # 数据库连接
│   └── log.py                   # 日志系统
├── docs/                        # 文档
│   ├── message_queue_usage.md
│   ├── scheduler_usage.md
│   └── README.md               # 本文档
├── main.py                      # 主应用入口
├── test_message_queue.py        # 消息队列测试
├── test_scheduler.py            # 调度器测试
├── pyproject.toml              # 项目配置
└── README.md                    # 项目说明
```

### 添加新的任务类型

1. **定义任务处理函数**

```python
def process_download_audio(params):
    url = params.get("url")
    save_path = params.get("save_path")
    # 下载逻辑
    download_audio(url, save_path)
```

2. **在Worker中注册处理器**

```python
task_handlers = {
    "download_audio": process_download_audio,
    "convert_format": process_convert_format,
    # 添加新类型...
}

def worker():
    while True:
        task = pop_task()
        if task:
            handler = task_handlers.get(task["type"])
            if handler:
                handler(task["params"])
```

3. **使用调度器或队列推入任务**

```python
# 立即执行
push_task({
    "type": "download_audio",
    "params": {"url": "...", "save_path": "..."}
})

# 定时执行
scheduler.add_scheduler_task(
    name="定期下载",
    task_type="download_audio",
    schedule_type="interval",
    interval_seconds=3600,
    params={"url": "...", "save_path": "..."}
)
```

### 数据库表说明

#### music 表 - 音乐信息
- `uuid` (主键) - 音乐唯一标识
- `md5` (唯一索引) - 文件MD5,用于去重
- `name` - 歌曲名称
- `author` - 艺术家
- `album` - 专辑
- `duration` - 时长(秒)
- `size` - 文件大小(字节)
- `bitrate` - 比特率(kbps)
- `cover_uuid` - 封面UUID
- `lyric` - 歌词内容
- `play_count` - 播放次数

#### scheduler_task 表 - 定时任务
- `task_id` (主键) - 任务ID
- `name` - 任务名称
- `task_type` - 任务类型
- `schedule_type` - 调度类型(interval/cron/once)
- `interval_seconds` - 间隔秒数
- `cron_expression` - Cron表达式
- `enabled` - 是否启用
- `run_count` - 执行次数
- `max_runs` - 最大执行次数

#### task_queue 表 - 任务队列持久化
- `task_id` (主键) - 任务ID
- `task_type` - 任务类型
- `status` - 任务状态(pending/processing/completed/failed)
- `scheduler_task_id` - 来源调度任务ID

---

## 🧪 测试 / Testing

### 测试消息队列
```bash
python test_message_queue.py
```

### 测试调度器
```bash
python test_scheduler.py
```

### 测试文件名解析
```bash
python -m app.utils.music_filename_parser
```

### 测试音乐扫描
```python
from app.utils.music_scanner import scan_and_import_folder

scan_and_import_folder("/path/to/music", skip_existing=False)
```

---

## 📝 最佳实践 / Best Practices

### 1. 音乐导入流程

```python
# 步骤1: 扫描文件夹
from app.utils.music_scanner import scan_and_import_folder

scan_and_import_folder(
    folder_path="/music/new",
    skip_existing=True,
    upgrade_quality=True
)

# 步骤2: 验证导入结果
from app.services.music_service import query_music
from app.database import SessionLocal

db = SessionLocal()
musics = query_music(db, page=1, page_size=10)
print(f"共导入 {len(musics)} 首音乐")
db.close()
```

### 2. 定时下载B站音乐

```python
from app.core.scheduler import get_scheduler
from app.core.message_queue import set_public

scheduler = get_scheduler()

# 设置cookie
set_public("bilibili_cookie", "SESSDATA=xxx", ttl=86400)

# 每天凌晨2点下载收藏夹
scheduler.add_scheduler_task(
    name="每日B站收藏夹下载",
    task_type="download_bilibili_favorites",
    schedule_type="cron",
    cron_expression="0 2 * * *",
    params={"favorites_id": "123456"},
    description="每天凌晨2点自动下载B站收藏夹"
)
```

### 3. Worker最佳实践

```python
import threading
from app.core.message_queue import get_queue
from app.log import logger

def worker(worker_id):
    queue = get_queue()
    logger.info(f"Worker-{worker_id} started")
    
    while True:
        try:
            task = queue.pop_task(timeout=5)
            if task:
                task_type = task["type"]
                params = task["params"]
                
                # 处理任务
                if task_type == "download_audio":
                    download_audio(**params)
                elif task_type == "convert_format":
                    convert_format(**params)
                
                queue.task_done()
                logger.success(f"Worker-{worker_id} completed task")
                
        except Exception as e:
            logger.error(f"Worker-{worker_id} error: {e}")

# 启动多个Worker
for i in range(3):
    threading.Thread(target=worker, args=(i,), daemon=True).start()
```

---

## 🔮 未来计划 / Future Plans

- [ ] B站音乐下载功能完整实现
- [ ] 用户系统(登录、权限管理)
- [ ] 播放列表功能
- [ ] 音乐推荐算法
- [ ] Web前端界面
- [ ] 音频波形图生成
- [ ] 完整Cron支持(croniter)
- [ ] Redis队列支持(可选)
- [ ] Docker部署支持
- [ ] API限流和缓存

---

## 📚 相关文档 / Related Documentation

- [消息队列使用文档](./message_queue_usage.md)
- [定时任务调度器文档](./scheduler_usage.md)

---

## 🤝 贡献 / Contributing

欢迎提交Issue和Pull Request!

## 📄 License

MIT License
