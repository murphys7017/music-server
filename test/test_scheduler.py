"""
定时任务调度器测试示例 / Scheduler Test Example
"""

import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import threading
from app.core.scheduler import get_scheduler
from app.core.message_queue import get_queue
from app.log import logger
from app.database import engine, Base


def worker():
    """
    工作线程,处理队列中的任务 / Worker thread to process queue tasks
    """
    queue = get_queue()
    logger.info("Worker 已启动 / Worker started")
    
    while True:
        task = queue.pop_task(timeout=5)
        if task:
            task_id = task.get("task_id")
            task_type = task.get("type")
            params = task.get("params", {})
            scheduler_task_name = task.get("scheduler_task_name", "Unknown")
            
            logger.info(f"[Worker] 处理任务 / Processing task: {task_id} [{task_type}]")
            logger.info(f"  来源调度任务 / From scheduler: {scheduler_task_name}")
            logger.info(f"  参数 / Params: {params}")
            
            # 模拟任务处理
            time.sleep(1)
            
            queue.task_done()
            logger.success(f"[Worker] 任务完成 / Task completed: {task_id}")


def test_interval_task():
    """测试间隔调度任务 / Test interval scheduling"""
    logger.info("\n===== 测试1: 间隔调度任务 / Test 1: Interval Scheduling =====")
    
    scheduler = get_scheduler()
    
    # 添加每30秒执行一次的任务
    task_id = scheduler.add_scheduler_task(
        name="定期下载B站音乐",
        task_type="download_bilibili_audio",
        schedule_type="interval",
        interval_seconds=30,
        params={
            "bv_id": "BV1xx411c7XZ",
            "quality": "320k"
        },
        max_runs=5,  # 最多执行5次
        description="每30秒下载一次B站音乐,共执行5次"
    )
    
    logger.info(f"已添加间隔任务 / Added interval task: {task_id}")
    
    # 查看任务详情
    task_info = scheduler.get_task(task_id)
    logger.info(f"任务详情 / Task details: {task_info}")
    
    return task_id


def test_once_task():
    """测试单次执行任务 / Test one-time execution"""
    logger.info("\n===== 测试2: 单次执行任务 / Test 2: One-time Execution =====")
    
    scheduler = get_scheduler()
    
    # 添加5秒后执行一次的任务
    execute_at = int(time.time()) + 5
    
    task_id = scheduler.add_scheduler_task(
        name="单次音频转换",
        task_type="convert_audio_format",
        schedule_type="once",
        execute_at=execute_at,
        params={
            "input_file": "/music/song.mp3",
            "output_format": "flac"
        },
        description="5秒后执行一次音频转换"
    )
    
    logger.info(f"已添加单次任务 / Added one-time task: {task_id}")
    logger.info(f"将在5秒后执行 / Will execute in 5 seconds")
    
    return task_id


def test_cron_task():
    """测试Cron表达式任务 / Test Cron expression"""
    logger.info("\n===== 测试3: Cron表达式任务 / Test 3: Cron Expression =====")
    
    scheduler = get_scheduler()
    
    # 添加每5分钟执行一次的任务
    task_id = scheduler.add_scheduler_task(
        name="定期清理临时文件",
        task_type="cleanup_temp_files",
        schedule_type="cron",
        cron_expression="*/5 * * * *",  # 每5分钟
        params={
            "temp_dir": "/tmp/music"
        },
        description="每5分钟清理一次临时文件"
    )
    
    logger.info(f"已添加Cron任务 / Added cron task: {task_id}")
    
    return task_id


def test_task_management():
    """测试任务管理功能 / Test task management"""
    logger.info("\n===== 测试4: 任务管理 / Test 4: Task Management =====")
    
    scheduler = get_scheduler()
    
    # 添加测试任务
    task_id = scheduler.add_scheduler_task(
        name="测试管理任务",
        task_type="test_task",
        schedule_type="interval",
        interval_seconds=10,
        params={"test": "value"},
        description="用于测试管理功能"
    )
    
    logger.info(f"已添加任务 / Added task: {task_id}")
    
    # 列出所有任务
    time.sleep(1)
    all_tasks = scheduler.list_tasks()
    logger.info(f"所有任务数量 / Total tasks: {len(all_tasks)}")
    for task in all_tasks:
        logger.info(f"  - {task['name']} [{task['task_id'][:8]}...] enabled={task['enabled']}")
    
    # 暂停任务
    logger.info(f"\n暂停任务 / Pausing task: {task_id}")
    scheduler.pause_task(task_id)
    time.sleep(1)
    
    # 查看任务状态
    task_info = scheduler.get_task(task_id)
    if task_info:
        logger.info(f"任务状态 / Task status: enabled={task_info['enabled']}")
    
    # 恢复任务
    logger.info(f"\n恢复任务 / Resuming task: {task_id}")
    scheduler.resume_task(task_id)
    time.sleep(1)
    
    # 再次查看状态
    task_info = scheduler.get_task(task_id)
    if task_info:
        logger.info(f"任务状态 / Task status: enabled={task_info['enabled']}")
    
    # 删除任务
    logger.info(f"\n删除任务 / Deleting task: {task_id}")
    scheduler.delete_task(task_id)
    time.sleep(1)
    
    # 确认删除
    deleted_task = scheduler.get_task(task_id)
    logger.info(f"任务是否存在 / Task exists: {deleted_task is not None}")


def test_bilibili_download_scenario():
    """模拟B站音乐下载场景 / Simulate Bilibili download scenario"""
    logger.info("\n===== 测试5: B站下载场景 / Test 5: Bilibili Download Scenario =====")
    
    scheduler = get_scheduler()
    
    # 场景1: 每天凌晨2点下载收藏夹
    task1_id = scheduler.add_scheduler_task(
        name="每日下载B站收藏夹",
        task_type="download_bilibili_favorites",
        schedule_type="interval",
        interval_seconds=86400,  # 24小时
        params={
            "favorites_id": "123456",
            "quality": "320k",
            "save_dir": "/music/bilibili"
        },
        description="每天下载B站收藏夹中的新音乐"
    )
    
    # 场景2: 每小时检查关注UP主的新投稿
    task2_id = scheduler.add_scheduler_task(
        name="检查UP主新投稿",
        task_type="check_bilibili_uploader_new",
        schedule_type="interval",
        interval_seconds=3600,  # 1小时
        params={
            "uploader_ids": ["123", "456", "789"],
            "auto_download": True
        },
        description="每小时检查关注UP主的新音乐投稿"
    )
    
    # 场景3: 立即下载指定视频
    task3_id = scheduler.add_scheduler_task(
        name="立即下载指定视频",
        task_type="download_bilibili_audio",
        schedule_type="once",
        execute_at=int(time.time()) + 3,
        params={
            "bv_id": "BV1xx411c7XZ",
            "quality": "320k",
            "extract_cover": True,
            "extract_lyrics": True
        },
        description="3秒后立即下载指定B站视频音频"
    )
    
    logger.info(f"已创建B站下载场景任务 / Created Bilibili download tasks:")
    logger.info(f"  - 每日收藏夹下载: {task1_id}")
    logger.info(f"  - 每小时检查UP主: {task2_id}")
    logger.info(f"  - 立即下载视频: {task3_id}")


if __name__ == "__main__":
    try:
        # 创建数据库表
        logger.info("创建数据库表 / Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # 启动工作线程
        worker_thread = threading.Thread(target=worker, daemon=True)
        worker_thread.start()
        
        # 等待系统初始化
        time.sleep(2)
        
        # 运行测试
        test_interval_task()
        time.sleep(2)
        
        test_once_task()
        time.sleep(2)
        
        test_cron_task()
        time.sleep(2)
        
        test_task_management()
        time.sleep(2)
        
        test_bilibili_download_scenario()
        
        logger.success("\n所有测试已创建 / All tests created")
        logger.info("调度器正在运行,等待任务执行... / Scheduler is running, waiting for task execution...")
        logger.info("观察60秒后退出 / Observing for 60 seconds before exit...")
        
        # 保持运行观察任务执行
        time.sleep(60)
        
    except KeyboardInterrupt:
        logger.info("测试中断 / Test interrupted")
    except Exception as e:
        logger.error(f"测试失败 / Test failed: {e}", exc_info=True)
