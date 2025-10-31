# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added - 2025-11-01

#### 消息队列 + 定时任务系统 / Message Queue + Scheduler System
**开发背景**: 通过 GitHub Copilot Chat 对话协作完成

**核心功能**:
- 🎯 **消息队列系统** (`app/core/message_queue.py`, 320行)
  - 线程安全的任务队列 (queue.Queue)
  - 公共信息存储 (支持 TTL 过期)
  - 自动清理后台线程
  - 全局单例模式
  
- ⏰ **定时任务调度器** (`app/core/scheduler.py`, 540行)
  - 支持三种调度类型: interval, cron, once
  - 数据库持久化 (系统重启后继续执行)
  - 动态任务管理 (添加/暂停/恢复/删除)
  - 自动推入消息队列
  
- 💾 **数据库模型** (`app/models/scheduler_task.py`, 100行)
  - SchedulerTask 表 - 定时任务配置
  - TaskQueue 表 - 任务队列持久化

**文档系统**:
- 📚 `docs/message_queue_usage.md` - 完整的消息队列使用文档
  - 项目复用指南 (6步复用流程)
  - 完整文件清单 (总计 ~1040 行代码)
  - 一键启动脚本模板
  - 常见问题 FAQ
  
- 📚 `docs/scheduler_usage.md` - 定时调度器详细文档
  - 三种调度类型详解
  - 任务管理 API
  - Cron 表达式说明
  - 工作流程图
  
- 📚 `docs/README.md` - 完整系统文档
  - 系统架构图
  - 快速开始指南
  - 开发指南和最佳实践

**测试系统**:
- 🧪 `test/test_message_queue.py` - 消息队列完整测试
- 🧪 `test/test_scheduler.py` - 调度器完整测试
- 📝 `test/README.md` - 测试说明文档

**技术特点**:
- ✅ 零外部依赖 (不依赖 Redis/RabbitMQ)
- ✅ 纯 Python 实现 (标准库 + SQLAlchemy)
- ✅ 线程安全设计
- ✅ 完整日志系统 (loguru)
- ✅ 易于复用和扩展

**AI 协助内容**:
1. 系统架构设计
2. 核心代码实现 (~1000 行)
3. SQLAlchemy 类型错误修复 (20+ 处)
4. 完整文档编写 (含中英双语)
5. 测试代码和测试组织
6. 项目复用指南

**应用场景**:
- B站音乐定期下载
- 音频格式批量转换
- 文件定期清理
- 数据定时同步
- 其他需要任务调度的场景

---

#### 音乐路由系统 / Music Router System
**开发背景**: 通过 GitHub Copilot Chat 完成

**功能**:
- 🎵 音乐列表 API (分页查询)
- 🔍 音乐搜索 API (模糊搜索)
- 📊 音乐详情 API
- 🎧 音乐播放 API (流式传输 + 播放次数统计)
- 🎨 封面获取 API (UUID-based)
- 📝 歌词获取 API

**技术要点**:
- FastAPI 路由系统
- SQLAlchemy 类型安全处理
- 文件流式响应
- 数据库查询优化

---

#### 音乐扫描工具 / Music Scanner
**开发背景**: 通过 GitHub Copilot Chat 完成

**功能**:
- 🔍 自动扫描文件夹
- 🎵 音频元数据提取 (Mutagen)
- 🎨 内嵌封面提取 (ID3/FLAC)
- 📝 内嵌歌词提取
- 📁 外部封面/歌词关联
- 🔄 MD5 去重
- ⬆️ 质量升级机制
- 💾 数据库批量导入

**文件**:
- `app/utils/music_scanner.py` - 核心扫描逻辑
- `app/utils/music_filename_parser.py` - 文件名解析
- `app/services/music_service.py` - 数据库服务

---

### Changed - 2025-11-01

#### 项目结构优化
- 📁 创建 `test/` 目录,统一管理测试文件
- 🔧 测试文件添加自动路径处理
- 📚 更新所有文档中的测试路径引用

---

### Fixed - 2025-11-01

#### SQLAlchemy 类型错误修复
- 🐛 修复 Column 对象的布尔判断问题 (使用 getattr)
- 🐛 修复 Column 属性赋值问题 (使用 setattr)
- 🐛 修复音乐路由中的类型检查错误 (20+ 处)
- 🐛 修复调度器中的类型检查错误 (20+ 处)

---

## Git 提交建议

### 提交1: 核心系统
```bash
git add app/core/message_queue.py app/core/scheduler.py app/models/scheduler_task.py
git commit -m "feat: 添加消息队列和定时任务调度系统

- 实现 MemoryQueue 消息队列 (320行)
- 实现 Scheduler 调度器 (540行)
- 添加数据库模型 (100行)
- 支持 interval/cron/once 三种调度
- 数据库持久化和自动恢复

Co-authored-by: GitHub Copilot
Ref: Chat 2025-11-01"
```

### 提交2: 文档系统
```bash
git add docs/
git commit -m "docs: 完善消息队列和调度器文档

- 添加完整使用文档 (message_queue_usage.md)
- 添加调度器文档 (scheduler_usage.md)
- 添加系统总览文档 (README.md)
- 包含项目复用指南和 FAQ

Co-authored-by: GitHub Copilot"
```

### 提交3: 测试组织
```bash
git add test/ run_test.py
git commit -m "test: 重组测试文件结构

- 创建 test/ 目录统一管理测试
- 添加测试说明文档 (test/README.md)
- 测试文件添加自动路径处理
- 更新文档中的测试路径引用

Co-authored-by: GitHub Copilot"
```

### 提交4: 集成
```bash
git add main.py
git commit -m "feat: 集成调度器到主应用

- 启动时自动初始化调度器
- 与 FastAPI 应用无缝集成

Co-authored-by: GitHub Copilot"
```

---

## 对话记录存档建议

### 方式1: Git Notes (详细)
```bash
git notes add -m "完整对话要点:
1. 需求: 创建轻量级消息队列系统用于B站音乐下载
2. 迭代1: 实现基础消息队列
3. 迭代2: 添加定时任务调度器
4. 迭代3: 数据库持久化设计
5. 迭代4: 修复类型错误 (20+ 处)
6. 迭代5: 完善文档(含复用指南)
7. 迭代6: 测试组织优化
总代码量: ~1500 行
AI 参与度: 95%"
```

### 方式2: 提交信息中引用
在每次提交的 footer 添加:
```
Co-authored-by: GitHub Copilot
Context: AI-assisted development session 2025-11-01
Topic: Building reusable task queue and scheduler system
Files: 10+ files, ~1500 lines of code
```

---

## 历史版本

### v0.1.0 - 2025-11-01 (Before Message Queue)
- 基础 FastAPI 应用
- 音乐路由和数据库模型
- 音乐扫描工具

### v0.2.0 - 2025-11-01 (After Message Queue)
- 完整的消息队列系统
- 定时任务调度器
- 数据库持久化
- 完整文档系统
- 测试框架
