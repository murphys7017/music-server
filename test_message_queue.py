"""
消息队列测试示例 / Message Queue Test Example
"""

import threading
import time
from app.core.message_queue import get_queue, push_task, pop_task, set_public, get_public
from app.log import logger


def worker(worker_id: int, queue):
    """
    工作线程 / Worker thread
    处理任务队列中的任务
    """
    logger.info(f"Worker-{worker_id} 已启动 / Worker-{worker_id} started")
    
    while True:
        # 获取任务,超时3秒
        task = queue.pop_task(timeout=3)
        
        if task is None:
            continue
        
        task_id = task.get("task_id")
        task_type = task.get("type")
        params = task.get("params", {})
        
        logger.info(f"Worker-{worker_id} 正在处理任务 / Processing task: {task_id} [{task_type}]")
        
        try:
            # 模拟任务处理
            if task_type == "download_audio":
                url = params.get("url")
                save_path = params.get("save_path")
                logger.info(f"  下载音频 / Downloading: {url} -> {save_path}")
                time.sleep(2)  # 模拟下载时间
                
            elif task_type == "convert_format":
                input_file = params.get("input_file")
                output_format = params.get("output_format")
                logger.info(f"  转换格式 / Converting: {input_file} -> {output_format}")
                time.sleep(1)  # 模拟转换时间
                
            else:
                logger.warning(f"  未知任务类型 / Unknown task type: {task_type}")
            
            # 标记任务完成
            queue.task_done()
            logger.success(f"Worker-{worker_id} 任务完成 / Task completed: {task_id}")
            
        except Exception as e:
            logger.error(f"Worker-{worker_id} 任务失败 / Task failed: {e}")


def test_basic_queue():
    """测试基本队列功能 / Test basic queue functionality"""
    logger.info("\n===== 测试1: 基本队列功能 / Test 1: Basic Queue =====")
    
    queue = get_queue()
    
    # 推入任务
    task1_id = push_task({
        "type": "download_audio",
        "params": {
            "url": "https://example.com/song.mp3",
            "save_path": "/music/song.mp3"
        }
    })
    
    task2_id = push_task({
        "type": "convert_format",
        "params": {
            "input_file": "/music/song.mp3",
            "output_format": "flac"
        }
    })
    
    logger.info(f"队列大小 / Queue size: {queue.get_queue_size()}")
    
    # 启动工作线程
    thread = threading.Thread(
        target=worker,
        args=(1, queue),
        daemon=True
    )
    thread.start()
    
    # 等待任务完成
    time.sleep(5)


def test_public_store():
    """测试公共信息存储 / Test public data store"""
    logger.info("\n===== 测试2: 公共信息存储 / Test 2: Public Store =====")
    
    queue = get_queue()
    
    # 设置永久数据
    set_public("api_key", "abc123xyz")
    logger.info(f"API Key: {get_public('api_key')}")
    
    # 设置临时数据(5秒后过期)
    set_public("session_cookie", "cookie_value_123", ttl=5)
    logger.info(f"Session Cookie: {get_public('session_cookie')}")
    
    # 设置任务状态
    set_public("task_status", {
        "total": 10,
        "completed": 5,
        "failed": 1
    })
    logger.info(f"Task Status: {get_public('task_status')}")
    
    # 列出所有键
    logger.info(f"所有键 / All keys: {queue.list_keys()}")
    
    # 等待过期
    logger.info("等待5秒测试TTL / Waiting 5s for TTL test...")
    time.sleep(6)
    
    # 检查过期数据
    logger.info(f"Session Cookie (应该过期): {get_public('session_cookie')}")
    logger.info(f"API Key (不应过期): {get_public('api_key')}")
    
    # 清理
    queue.clear_store()
    logger.info(f"清空后存储大小 / Store size after clear: {queue.get_store_size()}")


def test_multi_workers():
    """测试多工作线程 / Test multiple workers"""
    logger.info("\n===== 测试3: 多工作线程 / Test 3: Multiple Workers =====")
    
    queue = get_queue()
    
    # 启动3个工作线程
    for i in range(3):
        thread = threading.Thread(
            target=worker,
            args=(i + 1, queue),
            daemon=True
        )
        thread.start()
    
    # 推入10个任务
    for i in range(10):
        push_task({
            "type": "download_audio",
            "params": {
                "url": f"https://example.com/song{i}.mp3",
                "save_path": f"/music/song{i}.mp3"
            }
        })
    
    logger.info(f"已推入10个任务 / Pushed 10 tasks")
    logger.info(f"当前队列大小 / Current queue size: {queue.get_queue_size()}")
    
    # 等待所有任务完成
    time.sleep(10)


def test_bilibili_download():
    """模拟B站音乐下载场景 / Simulate Bilibili music download"""
    logger.info("\n===== 测试4: B站下载场景 / Test 4: Bilibili Download =====")
    
    queue = get_queue()
    
    # 设置B站cookie
    set_public("bilibili_cookie", "SESSDATA=xxx; bili_jct=yyy", ttl=3600)
    
    # 设置下载配置
    set_public("download_config", {
        "quality": "320k",
        "format": "mp3",
        "save_dir": "/music/downloads"
    })
    
    # 推入下载任务
    bv_ids = ["BV1xx411c7XZ", "BV1yy411c7YZ", "BV1zz411c7ZZ"]
    
    download_config = get_public("download_config")
    for bv_id in bv_ids:
        task_id = push_task({
            "type": "download_bilibili_audio",
            "params": {
                "bv_id": bv_id,
                "quality": download_config["quality"] if download_config else "320k"
            }
        })
        
        # 存储任务状态
        set_public(f"task_{task_id}_status", "pending")
    
    logger.info(f"已创建 {len(bv_ids)} 个B站下载任务 / Created {len(bv_ids)} Bilibili download tasks")
    
    cookie = get_public('bilibili_cookie')
    if cookie:
        logger.info(f"Cookie: {cookie[:30]}...")
    
    logger.info(f"配置 / Config: {download_config}")


if __name__ == "__main__":
    try:
        # 运行测试
        test_basic_queue()
        test_public_store()
        test_multi_workers()
        test_bilibili_download()
        
        logger.success("\n所有测试完成 / All tests completed")
        
        # 保持程序运行一段时间观察日志
        time.sleep(5)
        
    except KeyboardInterrupt:
        logger.info("测试中断 / Test interrupted")
    except Exception as e:
        logger.error(f"测试失败 / Test failed: {e}")
