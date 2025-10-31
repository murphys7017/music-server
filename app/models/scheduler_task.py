"""
定时任务数据库模型 / Scheduler Task Database Model
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, BigInteger
from app.database import Base


class SchedulerTask(Base):
    """定时任务表 / Scheduler Task Table"""
    
    __tablename__ = "scheduler_task"
    
    # 任务ID (主键) / Task ID (Primary Key)
    task_id = Column(String(36), primary_key=True, comment="任务ID")
    
    # 任务名称 / Task Name
    name = Column(String(255), nullable=False, comment="任务名称")
    
    # 任务类型 / Task Type
    task_type = Column(String(100), nullable=False, comment="任务类型")
    
    # 任务参数(JSON格式) / Task Parameters (JSON)
    params = Column(Text, nullable=True, comment="任务参数JSON")
    
    # 调度类型: interval(间隔), cron(Cron表达式), once(单次) / Schedule Type
    schedule_type = Column(String(20), nullable=False, default="interval", comment="调度类型")
    
    # 间隔时间(秒) / Interval in seconds
    interval_seconds = Column(Integer, nullable=True, comment="间隔时间(秒)")
    
    # Cron表达式 / Cron expression
    cron_expression = Column(String(100), nullable=True, comment="Cron表达式")
    
    # 指定执行时间(时间戳) / Specific execution time (timestamp)
    execute_at = Column(BigInteger, nullable=True, comment="指定执行时间戳")
    
    # 上次执行时间(时间戳) / Last execution time (timestamp)
    last_run_at = Column(BigInteger, nullable=True, comment="上次执行时间戳")
    
    # 下次执行时间(时间戳) / Next execution time (timestamp)
    next_run_at = Column(BigInteger, nullable=True, comment="下次执行时间戳")
    
    # 执行次数 / Execution count
    run_count = Column(Integer, default=0, comment="执行次数")
    
    # 最大执行次数(0表示无限制) / Max execution count (0 = unlimited)
    max_runs = Column(Integer, default=0, comment="最大执行次数")
    
    # 是否启用 / Is enabled
    enabled = Column(Boolean, default=True, comment="是否启用")
    
    # 创建时间(时间戳) / Created time (timestamp)
    created_at = Column(BigInteger, nullable=False, comment="创建时间戳")
    
    # 更新时间(时间戳) / Updated time (timestamp)
    updated_at = Column(BigInteger, nullable=False, comment="更新时间戳")
    
    # 备注 / Description
    description = Column(Text, nullable=True, comment="备注说明")


class TaskQueue(Base):
    """任务队列持久化表 / Task Queue Persistence Table"""
    
    __tablename__ = "task_queue"
    
    # 任务ID (主键) / Task ID (Primary Key)
    task_id = Column(String(36), primary_key=True, comment="任务ID")
    
    # 任务类型 / Task Type
    task_type = Column(String(100), nullable=False, comment="任务类型")
    
    # 任务参数(JSON格式) / Task Parameters (JSON)
    params = Column(Text, nullable=True, comment="任务参数JSON")
    
    # 任务状态: pending, processing, completed, failed / Task Status
    status = Column(String(20), default="pending", comment="任务状态")
    
    # 优先级(数字越大优先级越高) / Priority (higher number = higher priority)
    priority = Column(Integer, default=0, comment="优先级")
    
    # 重试次数 / Retry count
    retry_count = Column(Integer, default=0, comment="重试次数")
    
    # 最大重试次数 / Max retry count
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # 创建时间(时间戳) / Created time (timestamp)
    created_at = Column(BigInteger, nullable=False, comment="创建时间戳")
    
    # 开始处理时间(时间戳) / Started processing time (timestamp)
    started_at = Column(BigInteger, nullable=True, comment="开始处理时间戳")
    
    # 完成时间(时间戳) / Completed time (timestamp)
    completed_at = Column(BigInteger, nullable=True, comment="完成时间戳")
    
    # 错误信息 / Error message
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 来源调度任务ID / Source scheduler task ID
    scheduler_task_id = Column(String(36), nullable=True, comment="来源调度任务ID")
