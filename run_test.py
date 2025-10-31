"""
测试运行脚本 / Test Runner Script

用于从项目根目录运行测试文件
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="运行测试")
    parser.add_argument("test_file", help="测试文件名 (例如: test_scheduler 或 test_message_queue)")
    args = parser.parse_args()
    
    # 导入并运行测试
    test_module = f"test.{args.test_file}"
    print(f"运行测试: {test_module}")
    print("=" * 60)
    
    try:
        __import__(test_module)
    except Exception as e:
        print(f"测试失败: {e}")
        sys.exit(1)
