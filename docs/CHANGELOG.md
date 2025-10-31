# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added - 2025-11-01

#### 缩略图系统 / Thumbnail System
**开发背景**: 通过 GitHub Copilot Chat 完成

**核心功能**:
- 🖼️ **缩略图生成工具** (`app/utils/thumbnail_generator.py`, 200行)
  - 自动生成 200x200 缩略图
  - JPEG 格式压缩 (质量85)
  - 处理透明背景自动转换
  - 保持宽高比 (LANCZOS 重采样)
  - 批量生成和单独生成支持
  
- 🔄 **扫描器集成** (`app/utils/music_scanner.py`)
  - 扫描音乐时自动生成缩略图
  - 现有封面批量转换 (6个成功)
  
- 🌐 **API 接口** (`app/routers/music.py`)
  - 新增 `GET /music/thumbnail/{cover_uuid}` 接口
  - `/music/list` 返回 `thumbnail_url`，移除 `lyric`
  - `/music/search` 返回 `thumbnail_url`，移除 `lyric`
  - `/music/detail/{uuid}` 返回 `thumbnail_url` 和 `lyric`

**配置**:
- `THUMBNAIL_DIR` - 缩略图存储目录
- `THUMBNAIL_SIZE` - 缩略图尺寸 (200x200)
- `THUMBNAIL_QUALITY` - JPEG 压缩质量 (85)

**技术特点**:
- ✅ 文件体积优化 (~20KB vs 原图 >100KB)
- ✅ 统一 JPEG 格式输出
- ✅ 自动创建目录结构
- ✅ 跳过已存在的缩略图

**依赖**:
- Pillow 12.0.0

---

#### 环境变量管理 / Environment Variable Management
**开发背景**: 通过 GitHub Copilot Chat 完成

**核心功能**:
- 🔐 **python-dotenv 集成**
  - `app/config.py` 加载 .env 配置
  - `app/database.py` 加载 .env 配置
  - 统一环境变量管理
  
- 📝 **配置文件**
  - `.env.example` - 配置模板 (可提交)
  - `.env` - 实际配置 (已添加到 .gitignore)
  
**配置项**:
```bash
# 音乐目录
MUSIC_DIR, LYRICS_DIR, COVER_DIR, THUMBNAIL_DIR

# 数据库
MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

# 认证
STATIC_TOKEN
```

**技术特点**:
- ✅ 敏感信息与代码分离
- ✅ 多环境配置支持
- ✅ 安全的密码管理

**依赖**:
- python-dotenv 1.2.1

---

#### 歌词搜索功能 / Lyric Search Feature
**开发背景**: 通过 GitHub Copilot Chat 完成

**核心功能**:
- 🔍 **歌词搜索服务** (`app/services/music_service.py`)
  - `search_music_by_lyric()` - 根据歌词内容搜索
  - 自动过滤无歌词音乐
  - 支持模糊匹配和分页
  
- 🌐 **API 接口** (`app/routers/music.py`)
  - 新增 `GET /music/search/lyric` 接口
  - 参数: `keyword`, `page`, `page_size`
  - 返回完整歌词（方便前端高亮匹配部分）

**使用示例**:
```bash
GET /music/search/lyric?keyword=love&page=1&page_size=10
```

**技术特点**:
- ✅ LIKE 模糊匹配
- ✅ 自动过滤空歌词
- ✅ 返回完整歌词信息
- ✅ 支持分页查询

---

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

#### 搜索功能优化 / Search Optimization
- � 修复 `/music/search` API 的 OR 查询逻辑
  - 原逻辑: AND 条件（所有字段都匹配才返回）
  - 新逻辑: OR 条件（任意字段匹配即返回）
  - 使用 `sqlalchemy.or_()` 组合条件

#### 调度器性能优化 / Scheduler Performance
- ⚡ 优化定时任务查询策略
  - 原逻辑: 查询所有启用任务后逐个判断
  - 新逻辑: 只查询启用且已到期的任务
  - 添加数据库索引过滤 (`enabled=True AND next_run_at<=now`)
  - 添加调试日志显示到期任务数量
  - 显著减少数据库压力

---

### Fixed - 2025-11-01

#### SQLAlchemy 类型错误修复
- 🐛 修复 Column 对象的布尔判断问题 (使用 getattr)
- 🐛 修复 Column 属性赋值问题 (使用 setattr)
- 🐛 修复音乐路由中的类型检查错误 (20+ 处)
- 🐛 修复调度器中的类型检查错误 (20+ 处)

#### 类型注解错误修复
- 🐛 修复 `thumbnail_generator.py` 中的 Optional 类型注解
- 🐛 修复函数参数默认值为 None 的类型错误

#### 搜索逻辑错误修复
- 🐛 修复音乐搜索 API 使用 AND 逻辑导致结果为空
- 🐛 改为使用 OR 逻辑，任意字段匹配即返回结果

#### 项目结构优化
- 📁 创建 `test/` 目录,统一管理测试文件
- 🔧 测试文件添加自动路径处理
- 📚 更新所有文档中的测试路径引用

---

## Git 提交建议

### 本次提交 (2025-11-01): 缩略图 + 环境变量

#### 提交1: 缩略图功能
```bash
git add app/utils/thumbnail_generator.py app/config.py app/utils/music_scanner.py app/routers/music.py
git commit -m "feat: 添加缩略图生成系统

- 实现 thumbnail_generator 工具 (200行)
- 支持自动生成 200x200 JPEG 缩略图
- 集成到音乐扫描器自动生成
- 添加 /music/thumbnail/{uuid} API 接口
- list/search 接口返回 thumbnail_url，移除 lyric
- detail 接口返回 thumbnail_url 和 lyric
- 文件体积优化: ~20KB (原图 >100KB)

依赖: Pillow 12.0.0

Co-authored-by: GitHub Copilot
Context: AI-assisted development 2025-11-01"
```

#### 提交2: 环境变量管理
```bash
git add app/config.py app/database.py .env.example .gitignore
git commit -m "feat: 添加环境变量管理

- 集成 python-dotenv 统一管理配置
- 创建 .env.example 配置模板
- 数据库配置从环境变量读取
- .env 添加到 .gitignore 保护敏感信息

依赖: python-dotenv 1.2.1

Co-authored-by: GitHub Copilot"
```

#### 提交3: 测试和文档
```bash
git add test_thumbnail.py docs/CHANGELOG.md pyproject.toml
git commit -m "test: 添加缩略图测试并更新文档

- 添加缩略图功能测试脚本
- 更新 CHANGELOG 记录新功能
- 更新依赖: pillow, requests, python-dotenv

Co-authored-by: GitHub Copilot"
```

#### 提交4: 功能增强和优化
```bash
git add app/services/music_service.py app/routers/music.py app/core/scheduler.py
git commit -m "feat: 添加歌词搜索并优化性能

- 新增 /music/search/lyric API 接口
- 修复 /music/search 搜索逻辑（AND -> OR）
- 优化调度器只查询到期任务
- 添加调度器调试日志

Co-authored-by: GitHub Copilot"
```

---

### 历史提交建议 (消息队列系统)

#### 提交1: 核心系统
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

#### 提交2: 文档系统
```bash
git add docs/
git commit -m "docs: 完善消息队列和调度器文档

- 添加完整使用文档 (message_queue_usage.md)
- 添加调度器文档 (scheduler_usage.md)
- 添加系统总览文档 (README.md)
- 包含项目复用指南和 FAQ

Co-authored-by: GitHub Copilot"
```

#### 提交3: 测试组织
```bash
git add test/ run_test.py
git commit -m "test: 重组测试文件结构

- 创建 test/ 目录统一管理测试
- 添加测试说明文档 (test/README.md)
- 测试文件添加自动路径处理
- 更新文档中的测试路径引用

Co-authored-by: GitHub Copilot"
```

#### 提交4: 集成
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

### v0.2.0 - 2025-11-01 (Message Queue System)
- 完整的消息队列系统
- 定时任务调度器
- 数据库持久化
- 完整文档系统
- 测试框架

### v0.3.0 - 2025-11-01 (Thumbnail & Environment)
- 缩略图生成系统 (Pillow)
- 环境变量管理 (python-dotenv)
- 歌词搜索功能
- API 接口优化 (thumbnail_url)
- 配置文件管理 (.env)
- 搜索逻辑修复 (OR 条件)
- 调度器性能优化 (查询优化)
