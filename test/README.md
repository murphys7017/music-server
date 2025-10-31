# 测试文件说明 / Test Files Documentation

本目录包含项目的所有测试文件。

## 📁 测试文件列表 / Test Files

### 1. test_message_queue.py
**消息队列系统测试**

测试内容:
- ✅ 基本任务队列功能
- ✅ 公共信息存储
- ✅ TTL过期机制
- ✅ 多Worker并发处理
- ✅ B站下载场景模拟

运行测试:
```bash
python test/test_message_queue.py
```

### 2. test_scheduler.py
**定时任务调度器测试**

测试内容:
- ✅ 间隔调度任务 (interval)
- ✅ 单次执行任务 (once)
- ✅ Cron表达式任务 (cron)
- ✅ 任务管理功能 (暂停/恢复/删除)
- ✅ B站下载场景模拟

运行测试:
```bash
python test/test_scheduler.py
```

## 🚀 运行所有测试 / Run All Tests

### 方法1: 逐个运行
```bash
python test/test_message_queue.py
python test/test_scheduler.py
```

### 方法2: 使用测试框架 (可选)
```bash
# 安装 pytest
pip install pytest

# 运行所有测试
pytest test/

# 运行指定测试
pytest test/test_message_queue.py -v
```

## 📝 添加新测试 / Adding New Tests

1. 在 `test/` 目录下创建新的测试文件
2. 文件名以 `test_` 开头
3. 参考现有测试文件的结构

示例:
```python
# test/test_new_feature.py
from app.your_module import your_function
from app.log import logger

def test_basic_functionality():
    """测试基本功能"""
    result = your_function()
    assert result is not None
    logger.success("测试通过")

if __name__ == "__main__":
    test_basic_functionality()
```

## 🧪 测试最佳实践 / Testing Best Practices

1. **独立性**: 每个测试应该独立运行,不依赖其他测试
2. **清理**: 测试后清理创建的数据和资源
3. **日志**: 使用 logger 记录测试过程
4. **断言**: 使用 assert 验证测试结果
5. **文档**: 为每个测试函数添加说明

## 🔍 测试覆盖率 / Test Coverage

### 当前测试覆盖:
- ✅ 消息队列核心功能
- ✅ 定时任务调度器
- ✅ 任务队列管理
- ✅ 公共信息存储
- ⏳ API路由测试 (待添加)
- ⏳ 数据库操作测试 (待添加)
- ⏳ 音乐扫描功能测试 (待添加)

### 生成覆盖率报告 (可选):
```bash
pip install pytest-cov
pytest test/ --cov=app --cov-report=html
```

## 📊 测试结果示例 / Test Results Example

### test_message_queue.py 输出:
```
===== 测试1: 基本队列功能 =====
✓ 任务已推入队列: task-123
✓ Worker-1 处理任务完成
✓ 队列大小: 0

===== 测试2: 公共信息存储 =====
✓ API Key 已设置
✓ Session Cookie 已设置 (TTL: 5s)
✓ 5秒后过期测试通过

===== 测试3: 多工作线程 =====
✓ 已启动3个Worker
✓ 已推入10个任务
✓ 所有任务处理完成

✅ 所有测试完成
```

### test_scheduler.py 输出:
```
===== 测试1: 间隔调度任务 =====
✓ 已添加间隔任务: task-456
✓ 任务将每30秒执行一次

===== 测试2: 单次执行任务 =====
✓ 已添加单次任务: task-789
✓ 将在5秒后执行

===== 测试3: Cron表达式任务 =====
✓ 已添加Cron任务: task-abc
✓ 每5分钟执行一次

===== 测试4: 任务管理 =====
✓ 任务已暂停
✓ 任务已恢复
✓ 任务已删除

✅ 所有测试完成
```

## 🐛 调试测试 / Debugging Tests

### 启用详细日志:
```python
from app.log import logger

# 在测试文件顶部添加
logger.remove()
logger.add(sys.stdout, level="DEBUG")
```

### 使用断点调试:
```python
import pdb

def test_something():
    pdb.set_trace()  # 在此处暂停
    # 测试代码...
```

### VS Code 调试配置:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: 当前测试文件",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
```

## 📚 相关文档 / Related Documentation

- [消息队列使用文档](../docs/message_queue_usage.md)
- [定时调度器文档](../docs/scheduler_usage.md)
- [完整系统文档](../docs/README.md)
