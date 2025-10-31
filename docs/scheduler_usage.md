# 定时任务调度器使用文档 / Scheduler Usage Guide

## 📦 模块位置 / Module Location

```
app/core/scheduler.py
app/models/scheduler_task.py
```

## 🎯 功能特性 / Features

- ✅ **间隔调度** / Interval Scheduling - 按固定时间间隔执行任务
- ✅ **Cron表达式** / Cron Expression - 支持Cron表达式定时
- ✅ **单次执行** / One-time Execution - 指定时间执行一次
- ✅ **数据库持久化** / Database Persistence - 系统重启后任务继续执行
- ✅ **动态管理** / Dynamic Management - 添加、暂停、恢复、删除任务
- ✅ **任务队列集成** / Queue Integration - 自动推入任务到消息队列
- ✅ **执行次数限制** / Max Runs - 可设置最大执行次数

## 🚀 快速开始 / Quick Start

### 1. 初始化数据库表 / Initialize Database

```python
from app.database import engine, Base

# 创建调度器相关表
Base.metadata.create_all(bind=engine)
```

### 2. 获取调度器实例 / Get Scheduler Instance

```python
from app.core.scheduler import get_scheduler

scheduler = get_scheduler()  # 自动启动调度器
```

### 3. 添加定时任务 / Add Scheduled Task

#### 间隔任务 / Interval Task

```python
task_id = scheduler.add_scheduler_task(
    name="每30秒下载音乐",
    task_type="download_audio",
    schedule_type="interval",
    interval_seconds=30,
    params={
        "url": "https://example.com/song.mp3",
        "save_path": "/music/song.mp3"
    },
    max_runs=10,  # 最多执行10次
    description="每30秒下载一次音乐"
)
```

#### 单次任务 / One-time Task

```python
import time

# 5秒后执行
execute_at = int(time.time()) + 5

task_id = scheduler.add_scheduler_task(
    name="延迟下载",
    task_type="download_audio",
    schedule_type="once",
    execute_at=execute_at,
    params={"url": "..."},
    description="5秒后下载一次"
)
```

#### Cron任务 / Cron Task

```python
task_id = scheduler.add_scheduler_task(
    name="每小时整点执行",
    task_type="cleanup",
    schedule_type="cron",
    cron_expression="0 * * * *",  # 每小时0分
    params={"clean_dir": "/tmp"},
    description="每小时清理临时文件"
)
```

### 4. 管理任务 / Manage Tasks

```python
# 列出所有任务
all_tasks = scheduler.list_tasks()
for task in all_tasks:
    print(f"{task['name']}: enabled={task['enabled']}, run_count={task['run_count']}")

# 获取任务详情
task_info = scheduler.get_task(task_id)
print(task_info)

# 暂停任务
scheduler.pause_task(task_id)

# 恢复任务
scheduler.resume_task(task_id)

# 删除任务
scheduler.delete_task(task_id)
```

### 5. 处理任务 / Process Tasks

定时任务会自动生成普通任务并推入消息队列,需要启动Worker处理:

```python
import threading
from app.core.message_queue import get_queue

def worker():
    queue = get_queue()
    while True:
        task = queue.pop_task(timeout=5)
        if task:
            # 处理任务
            process_task(task)
            queue.task_done()

# 启动Worker线程
threading.Thread(target=worker, daemon=True).start()
```

## 📖 完整API / Full API

### Scheduler 类方法 / Class Methods

#### 调度器控制 / Scheduler Control

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `start()` | 启动调度器 | - |
| `stop()` | 停止调度器 | - |

#### 任务管理 / Task Management

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `add_scheduler_task()` | 添加定时任务 | 见下方详细说明 | `task_id: str` |
| `pause_task(task_id)` | 暂停任务 | `task_id: str` | `bool` |
| `resume_task(task_id)` | 恢复任务 | `task_id: str` | `bool` |
| `delete_task(task_id)` | 删除任务 | `task_id: str` | `bool` |
| `list_tasks(enabled_only)` | 列出任务 | `enabled_only: bool` | `List[Dict]` |
| `get_task(task_id)` | 获取任务详情 | `task_id: str` | `Dict\|None` |

#### add_scheduler_task 参数详解 / Parameters

```python
def add_scheduler_task(
    name: str,                          # 任务名称 / Task name
    task_type: str,                     # 任务类型 / Task type
    schedule_type: str,                 # 调度类型: interval/cron/once
    params: Optional[Dict] = None,      # 任务参数 / Task parameters
    interval_seconds: Optional[int] = None,  # 间隔秒数(interval类型)
    cron_expression: Optional[str] = None,   # Cron表达式(cron类型)
    execute_at: Optional[int] = None,   # 执行时间戳(once类型)
    max_runs: int = 0,                  # 最大执行次数(0=无限)
    description: Optional[str] = None   # 备注说明 / Description
) -> str:  # 返回任务ID / Returns task_id
```

## 🎯 使用场景 / Use Cases

### 场景1: B站音乐定期下载 / Periodic Bilibili Download

```python
from app.core.scheduler import get_scheduler
from app.core.message_queue import set_public

scheduler = get_scheduler()

# 设置B站cookie(公共存储)
set_public("bilibili_cookie", "SESSDATA=xxx; bili_jct=yyy", ttl=3600)

# 每天凌晨2点下载收藏夹
scheduler.add_scheduler_task(
    name="每日下载收藏夹",
    task_type="download_bilibili_favorites",
    schedule_type="interval",
    interval_seconds=86400,  # 24小时
    params={
        "favorites_id": "123456",
        "quality": "320k"
    },
    description="每天下载B站收藏夹新内容"
)

# 每小时检查UP主新投稿
scheduler.add_scheduler_task(
    name="检查UP主新投稿",
    task_type="check_uploader_new",
    schedule_type="interval",
    interval_seconds=3600,  # 1小时
    params={
        "uploader_ids": ["123", "456"],
        "auto_download": True
    },
    description="每小时检查并自动下载新投稿"
)
```

### 场景2: 音频格式批量转换 / Batch Audio Conversion

```python
# 每晚23点转换新下载的音频
scheduler.add_scheduler_task(
    name="批量音频转换",
    task_type="batch_convert_audio",
    schedule_type="cron",
    cron_expression="0 23 * * *",  # 每天23:00
    params={
        "input_dir": "/music/downloads",
        "output_format": "flac",
        "delete_original": False
    },
    description="每晚转换新下载的音频为FLAC格式"
)
```

### 场景3: 延迟任务 / Delayed Task

```python
import time

# 5分钟后执行清理
execute_at = int(time.time()) + 300

scheduler.add_scheduler_task(
    name="延迟清理",
    task_type="cleanup_temp_files",
    schedule_type="once",
    execute_at=execute_at,
    params={"temp_dir": "/tmp/music"},
    description="5分钟后清理临时文件"
)
```

### 场景4: 有限次数重复任务 / Limited Repeat Task

```python
# 每10秒执行一次,共执行5次
scheduler.add_scheduler_task(
    name="测试任务",
    task_type="test_download",
    schedule_type="interval",
    interval_seconds=10,
    max_runs=5,  # 只执行5次
    params={"test": "value"},
    description="测试任务,执行5次后自动停止"
)
```

## 📊 数据库表结构 / Database Schema

### scheduler_task 表 / Scheduler Task Table

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | VARCHAR(36) | 任务ID(主键) |
| `name` | VARCHAR(255) | 任务名称 |
| `task_type` | VARCHAR(100) | 任务类型 |
| `params` | TEXT | 任务参数(JSON) |
| `schedule_type` | VARCHAR(20) | 调度类型(interval/cron/once) |
| `interval_seconds` | INT | 间隔秒数 |
| `cron_expression` | VARCHAR(100) | Cron表达式 |
| `execute_at` | BIGINT | 指定执行时间戳 |
| `last_run_at` | BIGINT | 上次执行时间 |
| `next_run_at` | BIGINT | 下次执行时间 |
| `run_count` | INT | 执行次数 |
| `max_runs` | INT | 最大执行次数 |
| `enabled` | BOOLEAN | 是否启用 |
| `created_at` | BIGINT | 创建时间 |
| `updated_at` | BIGINT | 更新时间 |
| `description` | TEXT | 备注说明 |

### task_queue 表 / Task Queue Table

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | VARCHAR(36) | 任务ID(主键) |
| `task_type` | VARCHAR(100) | 任务类型 |
| `params` | TEXT | 任务参数(JSON) |
| `status` | VARCHAR(20) | 任务状态 |
| `priority` | INT | 优先级 |
| `retry_count` | INT | 重试次数 |
| `max_retries` | INT | 最大重试次数 |
| `created_at` | BIGINT | 创建时间 |
| `started_at` | BIGINT | 开始处理时间 |
| `completed_at` | BIGINT | 完成时间 |
| `error_message` | TEXT | 错误信息 |
| `scheduler_task_id` | VARCHAR(36) | 来源调度任务ID |

## ⚙️ 配置说明 / Configuration

### 检查间隔 / Check Interval

```python
from app.core.scheduler import Scheduler

# 自定义检查间隔(默认10秒)
scheduler = Scheduler(check_interval=5)  # 5秒检查一次
scheduler.start()
```

### Cron表达式格式 / Cron Expression Format

```
┌───────── 分钟 (0-59)
│ ┌─────── 小时 (0-23)
│ │ ┌───── 日期 (1-31)
│ │ │ ┌─── 月份 (1-12)
│ │ │ │ ┌─ 星期 (0-6, 0=周日)
│ │ │ │ │
* * * * *
```

**示例:**
- `"*/5 * * * *"` - 每5分钟
- `"0 * * * *"` - 每小时整点
- `"0 0 * * *"` - 每天凌晨
- `"0 2 * * *"` - 每天凌晨2点
- `"0 0 * * 0"` - 每周日凌晨

## 🔄 工作流程 / Workflow

```
┌─────────────┐
│ 添加定时任务  │
│  (数据库)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 调度器检查   │ ←─── 每N秒循环
│ (后台线程)   │
└──────┬──────┘
       │
       ▼ (任务到期)
┌─────────────┐
│ 生成普通任务  │
│ 推入消息队列  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Worker处理  │
│  (消费队列)  │
└─────────────┘
```

## 🧪 运行测试 / Run Tests

```bash
python test/test_scheduler.py
```

测试内容:
- ✅ 间隔调度任务
- ✅ 单次执行任务
- ✅ Cron表达式任务
- ✅ 任务管理(暂停/恢复/删除)
- ✅ B站下载场景模拟

## ⚠️ 注意事项 / Notes

1. **系统重启** - 定时任务保存在数据库,重启后自动恢复
2. **时间同步** - 确保服务器时间准确,避免任务错过
3. **任务队列** - 定时任务生成的普通任务需要Worker处理
4. **Cron实现** - 当前为简化实现,生产环境建议使用croniter库
5. **并发控制** - 调度器为单线程检查,任务执行在Worker中
6. **最大次数** - max_runs=0 表示无限执行,>0 表示执行指定次数后停止

## 🔮 未来扩展 / Future Extensions

- [ ] 完整Cron表达式支持(使用croniter)
- [ ] 任务优先级队列
- [ ] 任务执行失败重试
- [ ] 任务执行超时控制
- [ ] 任务执行历史记录
- [ ] 任务依赖关系
- [ ] Web界面管理
- [ ] 任务执行通知(邮件/webhook)

## 📝 完整示例 / Complete Example

查看 `test/test_scheduler.py` 获取完整示例代码。

## 🤝 与消息队列集成 / Integration with Message Queue

调度器与消息队列无缝集成:

```python
from app.core.scheduler import get_scheduler
from app.core.message_queue import get_queue, set_public, get_public

# 调度器自动使用全局消息队列
scheduler = get_scheduler()
queue = get_queue()

# 定时任务生成的普通任务会自动推入队列
# 可以共享公共信息存储
set_public("config", {"key": "value"})
config = get_public("config")
```
