"""
定时任务调度器 / Task Scheduler

支持间隔调度、Cron表达式、单次执行
Supports interval scheduling, Cron expressions, and one-time execution
"""

import json
import time
import threading
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.scheduler_task import SchedulerTask, TaskQueue
from app.core.message_queue import get_queue
from app.log import logger


class Scheduler:
    """
    定时任务调度器 / Task Scheduler
    
    特性 / Features:
    - 支持间隔调度 / Interval scheduling
    - 支持Cron表达式 / Cron expression support
    - 支持单次执行 / One-time execution
    - 数据库持久化 / Database persistence
    - 动态添加/删除任务 / Dynamic task management
    """
    
    def __init__(self, check_interval: int = 60):
        """
        初始化调度器
        
        Args:
            check_interval: 检查间隔(秒) / Check interval in seconds
        """
        self._check_interval = check_interval
        self._running = False
        self._scheduler_thread = None
        self._lock = threading.Lock()
        
        logger.info(f"调度器已初始化 / Scheduler initialized (check_interval={check_interval}s)")
    
    def start(self):
        """启动调度器 / Start scheduler"""
        if self._scheduler_thread is not None and self._scheduler_thread.is_alive():
            logger.warning("调度器已在运行 / Scheduler already running")
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_worker,
            daemon=True,
            name="Scheduler-Worker"
        )
        self._scheduler_thread.start()
        logger.info("调度器已启动 / Scheduler started")
    
    def stop(self):
        """停止调度器 / Stop scheduler"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=10)
            logger.info("调度器已停止 / Scheduler stopped")
    
    def _scheduler_worker(self):
        """调度器工作线程 / Scheduler worker thread"""
        logger.info("调度器工作线程已启动 / Scheduler worker thread started")
        
        while self._running:
            try:
                self._check_and_execute_tasks()
                time.sleep(self._check_interval)
            except Exception as e:
                logger.error(f"调度器异常 / Scheduler error: {e}", exc_info=True)
                time.sleep(5)
    
    def _check_and_execute_tasks(self):
        """检查并执行到期任务 / Check and execute due tasks"""
        db = SessionLocal()
        try:
            now = int(time.time())
            
            # 只查询启用且到期的任务，减少数据库压力
            # Query only enabled and due tasks to reduce database load
            tasks = db.query(SchedulerTask).filter(
                SchedulerTask.enabled == True,
                SchedulerTask.next_run_at <= now
            ).all()
            
            logger.debug(f"检查到 {len(tasks)} 个到期任务 / Found {len(tasks)} due tasks")
            
            for task in tasks:
                try:
                    self._execute_task(task, now, db)
                except Exception as e:
                    logger.error(f"执行任务失败 / Task execution failed [{task.task_id}]: {e}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"检查任务列表失败 / Task list check failed: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _should_execute(self, task: SchedulerTask, now: int) -> bool:
        """
        判断任务是否应该执行 / Check if task should execute
        
        Args:
            task: 定时任务对象 / Scheduled task object
            now: 当前时间戳 / Current timestamp
            
        Returns:
            should_execute: 是否应该执行 / Whether should execute
        """
        # 检查是否达到最大执行次数 / Check max runs
        max_runs = getattr(task, 'max_runs', 0)
        run_count = getattr(task, 'run_count', 0)
        if max_runs > 0 and run_count >= max_runs:
            return False
        
        # 首次执行 / First execution
        next_run_at = getattr(task, 'next_run_at', None)
        if next_run_at is None:
            return True
        
        # 检查是否到期 / Check if due
        return now >= next_run_at
    
    def _execute_task(self, task: SchedulerTask, now: int, db: Session):
        """
        执行定时任务 / Execute scheduled task
        
        Args:
            task: 定时任务对象 / Scheduled task object
            now: 当前时间戳 / Current timestamp
            db: 数据库会话 / Database session
        """
        try:
            # 解析任务参数 / Parse task parameters
            params_str = getattr(task, 'params', None)
            params = json.loads(params_str) if params_str else {}
            
            # 生成普通任务并推入队列 / Generate normal task and push to queue
            normal_task = {
                "task_id": str(uuid.uuid4()),
                "type": getattr(task, 'task_type'),
                "params": params,
                "scheduler_task_id": getattr(task, 'task_id'),
                "scheduler_task_name": getattr(task, 'name')
            }
            
            # 推入队列 / Push to queue
            queue = get_queue()
            task_id = queue.push_task(normal_task)
            
            # 可选:持久化到数据库 / Optional: Persist to database
            self._persist_task(normal_task, db)
            
            # 更新定时任务状态 / Update scheduled task status
            setattr(task, 'last_run_at', now)
            run_count = getattr(task, 'run_count', 0)
            setattr(task, 'run_count', run_count + 1)
            
            # 计算下次执行时间 / Calculate next run time
            next_run = self._calculate_next_run(task, now)
            setattr(task, 'next_run_at', next_run)
            
            # 如果是单次任务或达到最大次数,禁用任务 / Disable if one-time or max runs reached
            schedule_type = getattr(task, 'schedule_type')
            max_runs = getattr(task, 'max_runs', 0)
            if schedule_type == "once" or (max_runs > 0 and run_count + 1 >= max_runs):
                setattr(task, 'enabled', False)
                logger.info(f"定时任务已完成并禁用 / Scheduled task completed and disabled: {getattr(task, 'name')}")
            
            setattr(task, 'updated_at', now)
            
            logger.info(
                f"定时任务已执行 / Scheduled task executed: {getattr(task, 'name')} "
                f"[{getattr(task, 'task_id')}] -> Normal Task [{task_id}], "
                f"run_count={run_count + 1}, next_run_at={next_run}"
            )
            
        except Exception as e:
            logger.error(f"执行定时任务失败 / Execute scheduled task failed [{getattr(task, 'task_id')}]: {e}")
    
    def _calculate_next_run(self, task: SchedulerTask, now: int) -> Optional[int]:
        """
        计算下次执行时间 / Calculate next run time
        
        Args:
            task: 定时任务对象 / Scheduled task object
            now: 当前时间戳 / Current timestamp
            
        Returns:
            next_run_at: 下次执行时间戳 / Next run timestamp
        """
        schedule_type = getattr(task, 'schedule_type')
        
        if schedule_type == "once":
            return None
        
        elif schedule_type == "interval":
            interval_seconds = getattr(task, 'interval_seconds', None)
            if interval_seconds:
                return now + interval_seconds
            return None
        
        elif schedule_type == "cron":
            # 简化实现:支持基本Cron表达式解析
            # Simplified: Basic Cron expression parsing
            cron_expression = getattr(task, 'cron_expression', None)
            if cron_expression:
                return self._parse_cron_next_run(cron_expression, now)
            return None
        
        return None
    
    def _parse_cron_next_run(self, cron_expr: str, now: int) -> Optional[int]:
        """
        解析Cron表达式计算下次执行时间 / Parse Cron expression for next run
        
        简化实现,支持格式: "* * * * *" (分 时 日 月 周)
        Simplified implementation, supports: "minute hour day month weekday"
        
        Args:
            cron_expr: Cron表达式 / Cron expression
            now: 当前时间戳 / Current timestamp
            
        Returns:
            next_run_at: 下次执行时间戳 / Next run timestamp
        """
        try:
            # 这里提供一个简化实现,实际项目可以使用croniter库
            # This is a simplified implementation. Use croniter library in production.
            
            parts = cron_expr.split()
            if len(parts) != 5:
                logger.warning(f"无效的Cron表达式 / Invalid Cron expression: {cron_expr}")
                return None
            
            # 简单处理:如果是 "*/N * * * *" 格式,表示每N分钟执行
            # Simple handling: "*/N * * * *" means every N minutes
            if parts[0].startswith("*/"):
                minutes = int(parts[0][2:])
                return now + (minutes * 60)
            
            # 如果是 "0 * * * *" 格式,表示每小时整点执行
            # "0 * * * *" means every hour at minute 0
            if parts[0] == "0" and parts[1] == "*":
                current_dt = datetime.fromtimestamp(now)
                next_hour = current_dt.replace(minute=0, second=0, microsecond=0)
                next_hour = datetime(
                    next_hour.year, next_hour.month, next_hour.day,
                    next_hour.hour + 1, 0, 0
                )
                return int(next_hour.timestamp())
            
            # 默认1小时后执行 / Default: 1 hour later
            logger.warning(f"Cron表达式解析未完全实现,使用默认间隔 / Cron parsing not fully implemented: {cron_expr}")
            return now + 3600
            
        except Exception as e:
            logger.error(f"解析Cron表达式失败 / Parse Cron failed: {e}")
            return None
    
    def _persist_task(self, task: Dict[str, Any], db: Session):
        """
        持久化普通任务到数据库 / Persist normal task to database
        
        Args:
            task: 任务字典 / Task dict
            db: 数据库会话 / Database session
        """
        try:
            task_queue = TaskQueue(
                task_id=task["task_id"],
                task_type=task["type"],
                params=json.dumps(task.get("params", {})),
                status="pending",
                priority=task.get("priority", 0),
                created_at=int(time.time()),
                scheduler_task_id=task.get("scheduler_task_id")
            )
            db.add(task_queue)
            logger.debug(f"任务已持久化 / Task persisted: {task['task_id']}")
        except Exception as e:
            logger.error(f"持久化任务失败 / Persist task failed: {e}")
    
    # ========== 管理接口 / Management API ==========
    
    def add_scheduler_task(
        self,
        name: str,
        task_type: str,
        schedule_type: str,
        params: Optional[Dict[str, Any]] = None,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        execute_at: Optional[int] = None,
        max_runs: int = 0,
        description: Optional[str] = None
    ) -> str:
        """
        添加定时任务 / Add scheduled task
        
        Args:
            name: 任务名称 / Task name
            task_type: 任务类型 / Task type
            schedule_type: 调度类型 (interval/cron/once) / Schedule type
            params: 任务参数 / Task parameters
            interval_seconds: 间隔时间(秒) / Interval in seconds
            cron_expression: Cron表达式 / Cron expression
            execute_at: 指定执行时间戳 / Specific execution timestamp
            max_runs: 最大执行次数 / Max execution count
            description: 备注说明 / Description
            
        Returns:
            task_id: 任务ID / Task ID
        """
        db = SessionLocal()
        try:
            now = int(time.time())
            task_id = str(uuid.uuid4())
            
            # 计算首次执行时间 / Calculate first run time
            next_run_at = execute_at if execute_at else now
            
            task = SchedulerTask(
                task_id=task_id,
                name=name,
                task_type=task_type,
                params=json.dumps(params) if params else None,
                schedule_type=schedule_type,
                interval_seconds=interval_seconds,
                cron_expression=cron_expression,
                execute_at=execute_at,
                next_run_at=next_run_at,
                max_runs=max_runs,
                enabled=True,
                created_at=now,
                updated_at=now,
                description=description
            )
            
            db.add(task)
            db.commit()
            
            logger.info(f"定时任务已添加 / Scheduled task added: {name} [{task_id}]")
            return task_id
            
        except Exception as e:
            logger.error(f"添加定时任务失败 / Add scheduled task failed: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def pause_task(self, task_id: str) -> bool:
        """暂停定时任务 / Pause scheduled task"""
        db = SessionLocal()
        try:
            task = db.query(SchedulerTask).filter(SchedulerTask.task_id == task_id).first()
            if task:
                setattr(task, 'enabled', False)
                setattr(task, 'updated_at', int(time.time()))
                db.commit()
                logger.info(f"定时任务已暂停 / Scheduled task paused: {getattr(task, 'name')} [{task_id}]")
                return True
            return False
        except Exception as e:
            logger.error(f"暂停定时任务失败 / Pause task failed: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def resume_task(self, task_id: str) -> bool:
        """恢复定时任务 / Resume scheduled task"""
        db = SessionLocal()
        try:
            task = db.query(SchedulerTask).filter(SchedulerTask.task_id == task_id).first()
            if task:
                setattr(task, 'enabled', True)
                setattr(task, 'updated_at', int(time.time()))
                db.commit()
                logger.info(f"定时任务已恢复 / Scheduled task resumed: {getattr(task, 'name')} [{task_id}]")
                return True
            return False
        except Exception as e:
            logger.error(f"恢复定时任务失败 / Resume task failed: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def delete_task(self, task_id: str) -> bool:
        """删除定时任务 / Delete scheduled task"""
        db = SessionLocal()
        try:
            task = db.query(SchedulerTask).filter(SchedulerTask.task_id == task_id).first()
            if task:
                db.delete(task)
                db.commit()
                logger.info(f"定时任务已删除 / Scheduled task deleted: {task.name} [{task_id}]")
                return True
            return False
        except Exception as e:
            logger.error(f"删除定时任务失败 / Delete task failed: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def list_tasks(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        列出所有定时任务 / List all scheduled tasks
        
        Args:
            enabled_only: 仅列出启用的任务 / Only list enabled tasks
            
        Returns:
            tasks: 任务列表 / Task list
        """
        db = SessionLocal()
        try:
            query = db.query(SchedulerTask)
            if enabled_only:
                query = query.filter(SchedulerTask.enabled == True)
            
            tasks = query.all()
            
            result = []
            for task in tasks:
                result.append({
                    "task_id": task.task_id,
                    "name": task.name,
                    "task_type": task.task_type,
                    "schedule_type": task.schedule_type,
                    "enabled": task.enabled,
                    "run_count": task.run_count,
                    "max_runs": task.max_runs,
                    "last_run_at": task.last_run_at,
                    "next_run_at": task.next_run_at,
                    "created_at": task.created_at,
                    "description": task.description
                })
            
            return result
            
        finally:
            db.close()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取定时任务详情 / Get scheduled task details
        
        Args:
            task_id: 任务ID / Task ID
            
        Returns:
            task: 任务详情 / Task details
        """
        db = SessionLocal()
        try:
            task = db.query(SchedulerTask).filter(SchedulerTask.task_id == task_id).first()
            if not task:
                return None
            
            params_str = getattr(task, 'params', None)
            return {
                "task_id": getattr(task, 'task_id'),
                "name": getattr(task, 'name'),
                "task_type": getattr(task, 'task_type'),
                "params": json.loads(params_str) if params_str else {},
                "schedule_type": getattr(task, 'schedule_type'),
                "interval_seconds": getattr(task, 'interval_seconds'),
                "cron_expression": getattr(task, 'cron_expression'),
                "execute_at": getattr(task, 'execute_at'),
                "enabled": getattr(task, 'enabled'),
                "run_count": getattr(task, 'run_count'),
                "max_runs": getattr(task, 'max_runs'),
                "last_run_at": getattr(task, 'last_run_at'),
                "next_run_at": getattr(task, 'next_run_at'),
                "created_at": getattr(task, 'created_at'),
                "updated_at": getattr(task, 'updated_at'),
                "description": getattr(task, 'description')
            }
            
        finally:
            db.close()


# 全局单例 / Global singleton instance
_global_scheduler: Optional[Scheduler] = None
_scheduler_lock = threading.Lock()


def get_scheduler() -> Scheduler:
    """
    获取全局调度器实例 / Get global scheduler instance
    
    Returns:
        scheduler: 调度器实例 / Scheduler instance
    """
    global _global_scheduler
    
    if _global_scheduler is None:
        with _scheduler_lock:
            if _global_scheduler is None:
                _global_scheduler = Scheduler()
                _global_scheduler.start()
                logger.info("全局调度器已创建 / Global scheduler created")
    
    return _global_scheduler
