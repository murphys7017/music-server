"""
轻量级消息队列模块 / Lightweight Message Queue Module

提供基于内存的任务队列和公共信息存储功能
Provides in-memory task queue and shared data store functionality
"""

import queue
import threading
import time
import uuid
from typing import Any, Dict, Optional
from app.log import logger


class MemoryQueue:
    """
    内存消息队列 / In-Memory Message Queue
    
    特性 / Features:
    - 线程安全的任务队列 / Thread-safe task queue
    - 公共信息存储(支持TTL) / Shared data store with TTL support
    - 自动过期清理 / Automatic expiration cleanup
    """
    
    def __init__(self, cleanup_interval: int = 60):
        """
        初始化消息队列
        
        Args:
            cleanup_interval: 自动清理间隔(秒) / Auto cleanup interval in seconds
        """
        # 任务队列 / Task Queue
        self._task_queue = queue.Queue()
        
        # 公共信息存储 / Public Data Store
        # 格式: {key: {"value": Any, "expire_at": float | None}}
        self._public_store: Dict[str, Dict[str, Any]] = {}
        self._store_lock = threading.Lock()
        
        # 后台清理线程 / Background cleanup thread
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread = None
        self._running = False
        
        logger.info("消息队列已初始化 / Message queue initialized")
    
    def start_cleanup(self):
        """启动后台清理线程 / Start background cleanup thread"""
        if self._cleanup_thread is not None and self._cleanup_thread.is_alive():
            logger.warning("清理线程已在运行 / Cleanup thread already running")
            return
        
        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True,
            name="MessageQueue-Cleanup"
        )
        self._cleanup_thread.start()
        logger.info("后台清理线程已启动 / Cleanup thread started")
    
    def stop_cleanup(self):
        """停止后台清理线程 / Stop background cleanup thread"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
            logger.info("后台清理线程已停止 / Cleanup thread stopped")
    
    def _cleanup_worker(self):
        """后台清理工作线程 / Background cleanup worker"""
        while self._running:
            try:
                self.cleanup()
                time.sleep(self._cleanup_interval)
            except Exception as e:
                logger.error(f"清理线程异常 / Cleanup error: {e}")
    
    # ========== 任务队列接口 / Task Queue API ==========
    
    def push_task(self, task: Dict[str, Any]) -> str:
        """
        推入任务到队列 / Push task to queue
        
        Args:
            task: 任务字典，必须包含 type 字段
                  Task dict, must contain 'type' field
                  
        Returns:
            task_id: 任务ID / Task ID
        """
        if "task_id" not in task:
            task["task_id"] = str(uuid.uuid4())
        
        if "type" not in task:
            raise ValueError("任务必须包含 'type' 字段 / Task must contain 'type' field")
        
        self._task_queue.put(task)
        logger.info(f"任务已推入队列 / Task pushed: {task['task_id']} [{task['type']}]")
        return task["task_id"]
    
    def pop_task(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        从队列弹出任务 / Pop task from queue
        
        Args:
            timeout: 超时时间(秒)，None表示阻塞等待
                     Timeout in seconds, None for blocking wait
                     
        Returns:
            task: 任务字典，超时返回None / Task dict or None on timeout
        """
        try:
            task = self._task_queue.get(timeout=timeout)
            logger.info(f"任务已弹出 / Task popped: {task.get('task_id')} [{task.get('type')}]")
            return task
        except queue.Empty:
            return None
    
    def task_done(self):
        """标记任务完成 / Mark task as done"""
        self._task_queue.task_done()
    
    def get_queue_size(self) -> int:
        """获取队列中任务数量 / Get queue size"""
        return self._task_queue.qsize()
    
    def is_empty(self) -> bool:
        """检查队列是否为空 / Check if queue is empty"""
        return self._task_queue.empty()
    
    # ========== 公共信息存储接口 / Public Data Store API ==========
    
    def set_public(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置公共信息 / Set public data
        
        Args:
            key: 键名 / Key name
            value: 值 / Value
            ttl: 过期时间(秒)，None表示永不过期
                 Time to live in seconds, None for no expiration
        """
        expire_at = None if ttl is None else time.time() + ttl
        
        with self._store_lock:
            self._public_store[key] = {
                "value": value,
                "expire_at": expire_at
            }
        
        logger.debug(f"公共信息已设置 / Public data set: {key} (TTL: {ttl}s)")
    
    def get_public(self, key: str) -> Optional[Any]:
        """
        获取公共信息 / Get public data
        
        Args:
            key: 键名 / Key name
            
        Returns:
            value: 值，不存在或已过期返回None
                   Value or None if not exists or expired
        """
        with self._store_lock:
            if key not in self._public_store:
                return None
            
            entry = self._public_store[key]
            
            # 检查是否过期 / Check expiration
            if entry["expire_at"] is not None and time.time() > entry["expire_at"]:
                del self._public_store[key]
                logger.debug(f"公共信息已过期 / Public data expired: {key}")
                return None
            
            return entry["value"]
    
    def delete_public(self, key: str) -> bool:
        """
        删除公共信息 / Delete public data
        
        Args:
            key: 键名 / Key name
            
        Returns:
            success: 是否删除成功 / Whether deletion succeeded
        """
        with self._store_lock:
            if key in self._public_store:
                del self._public_store[key]
                logger.debug(f"公共信息已删除 / Public data deleted: {key}")
                return True
            return False
    
    def cleanup(self):
        """清理过期的公共信息 / Cleanup expired public data"""
        now = time.time()
        expired_keys = []
        
        with self._store_lock:
            for key, entry in self._public_store.items():
                if entry["expire_at"] is not None and now > entry["expire_at"]:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._public_store[key]
        
        if expired_keys:
            logger.info(f"已清理 {len(expired_keys)} 条过期信息 / Cleaned {len(expired_keys)} expired entries")
    
    def get_store_size(self) -> int:
        """获取公共信息存储数量 / Get store size"""
        with self._store_lock:
            return len(self._public_store)
    
    def list_keys(self) -> list:
        """列出所有公共信息的键 / List all public data keys"""
        with self._store_lock:
            return list(self._public_store.keys())
    
    def clear_store(self):
        """清空公共信息存储 / Clear all public data"""
        with self._store_lock:
            count = len(self._public_store)
            self._public_store.clear()
        logger.info(f"已清空 {count} 条公共信息 / Cleared {count} public data entries")


# 全局单例 / Global singleton instance
_global_queue: Optional[MemoryQueue] = None
_queue_lock = threading.Lock()


def get_queue() -> MemoryQueue:
    """
    获取全局消息队列实例 / Get global message queue instance
    
    Returns:
        queue: 消息队列实例 / Message queue instance
    """
    global _global_queue
    
    if _global_queue is None:
        with _queue_lock:
            if _global_queue is None:
                _global_queue = MemoryQueue()
                _global_queue.start_cleanup()
                logger.info("全局消息队列已创建 / Global message queue created")
    
    return _global_queue


# 便捷函数 / Convenience functions
def push_task(task: Dict[str, Any]) -> str:
    """推入任务 / Push task"""
    return get_queue().push_task(task)


def pop_task(timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """弹出任务 / Pop task"""
    return get_queue().pop_task(timeout)


def set_public(key: str, value: Any, ttl: Optional[int] = None):
    """设置公共信息 / Set public data"""
    get_queue().set_public(key, value, ttl)


def get_public(key: str) -> Optional[Any]:
    """获取公共信息 / Get public data"""
    return get_queue().get_public(key)


def delete_public(key: str) -> bool:
    """删除公共信息 / Delete public data"""
    return get_queue().delete_public(key)
