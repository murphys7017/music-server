user
帮我在app目录下添加一个log模块，使用loguru为全局提供日志记录系统

user
我需要使用sqlalchemy 连接MySQL数据库 ，帮我在app文件夹下面写一个database.py，提供数据库连接，等公共方法

user
下面我给你一些文件名例子：
玉盘 - 葫芦童声
Libertus - Chen-U_EG
Silent Street (Type A) - Hyunmin Cho _ seibin _ Youngkyoung Choi _ SHIFT UP
病名为爱 (国语) - 祖娅纳惜
どうして… (为什么) - 凋叶棕
BLUE DRAGON ('07 ver_) - 澤野弘之
像鱼 (伴奏) - 王贰浪
Let Her Go (DOAN Remix) - Doan
The Edge (Original Mix) - Grant _ Nevve
LEVEL5-judgelight- (instrumental) - fripSide
Ghost (The Him Remix) - Au_Ra _ Alan Walker
夢燈籠 (R7CKY 你的名字 Mix) - R7CKY
病名为爱-古风版 (改编版原唱_ Neru) - 杨可爱
RISE（中文版）登峰造极境（语言版） - 祈Inory
My Dearest (Instrumental_TV Edit) - supercell
All Alone With You (Inst_) - EGOIST
答案 (女声吉他弹唱) - 李瑨瑶
勾指起誓 (甜味小少年ver) - 洛少爷
等等还有很多

user
我的下一步计划是在app core中添加一个消息队列，这个消息队列要求如下：
# Python 轻量消息队列模块说明 / Python Lightweight Message Queue Specification

## 🎯 目标 / Goal

实现一个 **轻量、纯 Python 的消息队列系统**，不依赖 Redis 或数据库，仅使用标准库。
该系统主要用于 **管理 B 站音乐下载与处理任务**，并提供一个 **公共信息区** 用于临时或全局数据的存储。

Implement a **lightweight, self-contained Python message queue system** for a personal project.
No Redis, no database — everything runs purely in memory using the Python standard library.
The queue will manage **Bilibili music download and processing tasks**, and also store **temporary shared information**.

---

## 🧩 核心组件 / Core Components

### 1. 任务队列（Task Queue）

* 使用 `queue.Queue` 实现线程安全的任务存取。
* 每个任务是一个字典对象，例如：

  ```python
  {
      "task_id": "uuid",
      "type": "download_audio",
      "params": {"url": "...", "save_path": "..."}
  }
  ```
* 提供的接口 / API:

  * `push_task(task: dict)` — 推入任务
  * `pop_task(timeout=None) -> dict | None` — 弹出任务（阻塞或超时）
* 支持多线程消费者（worker）执行任务。

Thread-safe queue using `queue.Queue`.
Each task is a dict object with ID, type, and parameters.
Provides `push_task()` and `pop_task()` methods.
Supports multiple worker threads.

---

### 2. 公共信息存储（Public Data Store）

* 用于保存临时或全局信息（如 cookie、API 缓存、下载状态等）。
* 可以设置过期时间（TTL）或手动删除。
* 由系统或消费者决定何时清理或移除。
* 接口 / API:

  * `set_public(key: str, value: Any, ttl: int | None = None)` — 设置值，可选过期时间
  * `get_public(key: str) -> Any | None` — 获取值
  * `delete_public(key: str)` — 删除值
  * `cleanup()` — 清理过期数据

Used as a shared in-memory key-value store for global or temporary data.
Supports optional TTL or manual expiration.
System or consumers can decide when to clear.
Provides the same four APIs as above.

---

### 3. 内部特性 / Internal Features

* 使用 `threading.Lock` 确保线程安全。
* 可选后台线程定期清理过期信息。
* 可加入简单日志或打印输出任务执行状态。

Thread-safe via `threading.Lock`.
Optional background cleanup thread.
Supports simple logging or print output.

---

## 💡 示例使用 / Example Usage

```python
queue = MemoryQueue()
queue.push_task({"task_id": "1", "type": "download_audio", "params": {...}})
queue.set_public("current_session", {"cookie": "..."})

def worker(q):
    while True:
        task = q.pop_task(timeout=3)
        if task:
            print("Processing:", task["task_id"])
            # Perform download or conversion

threading.Thread(target=worker, args=(queue,), daemon=True).start()
```

---

## 🚀 未来扩展 / Future Extensions

* 任务优先级（Task priority）
* 任务状态追踪（Task state tracking）
* 文件持久化（File persistence）
* 回调系统（Event hooks or callback system）
* 可替换的后端实现（e.g., Redis, Database）

---

## ✅ 技术要点 / Key Technologies

* `queue.Queue` — 线程安全队列 / Thread-safe queue
* `threading` — 多线程执行 / Multithreading support
* `time` + `Lock` — TTL 管理 / TTL management
* `uuid` — 任务 ID 生成 / Task ID generation
* `logging` — 可选日志输出 / Optional logging system
