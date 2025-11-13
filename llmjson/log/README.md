# 日志模块文档

## 概述

新的日志模块提供了完整的日志管理功能，包括配置管理、单例模式、上下文日志、结构化日志等高级特性。

## 功能特点

### ✨ 核心特性
- 🔒 **单例模式**: 确保全局日志一致性
- ⚙️ **灵活配置**: 支持多种配置方式
- 🏷️ **上下文日志**: 支持带上下文信息的日志记录
- 📋 **结构化日志**: 支持JSON格式和结构化数据
- ⏱️ **计时功能**: 内置计时器和性能监控
- 🔄 **日志轮转**: 自动文件轮转和清理
- 🧵 **线程安全**: 支持多线程环境
- 🌍 **环境配置**: 支持不同环境的配置

### 📁 模块结构
```
logging/
├── __init__.py          # 模块入口
├── config.py            # 配置类
├── manager.py           # 日志管理器
├── context.py           # 上下文日志器
├── setup.py             # 设置函数
└── logging_config_example.json  # 配置示例
```

## 快速开始

### 基本使用

```python
from llmjson.log import setup_logging, get_logger

# 设置日志系统
logger = setup_logging(log_level="INFO")

# 记录日志
logger.info("这是一条信息日志")
logger.warning("这是一条警告")
logger.error("这是一条错误")

# 在其他地方获取日志器
logger = get_logger()
logger.info("使用相同的日志器实例")
```

### 自定义配置

```python
from llmjson.log import LogConfig, setup_logging

# 创建自定义配置
config = LogConfig()
config.log_level = "DEBUG"
config.max_file_size = 10 * 1024 * 1024  # 10MB
config.backup_count = 5
config.enable_json = True

# 使用自定义配置
logger = setup_logging(config=config)
```

### 上下文日志

```python
from llmjson.log import create_logger_with_context

# 创建带上下文的日志器
context = {
    'user_id': 'user_123',
    'session_id': 'session_456',
    'operation': 'document_processing'
}

context_logger = create_logger_with_context(context)
context_logger.info("处理文档开始")
context_logger.error("处理过程中遇到错误")
```

### 计时日志

```python
from llmjson.log import create_timed_logger

# 创建计时日志器
timed_logger = create_timed_logger({'operation': 'data_processing'})

# 开始计时
timed_logger.start_timer("process_data")
# ... 执行一些操作 ...
# 结束计时
elapsed = timed_logger.end_timer("process_data")
```

### 结构化日志

```python
from llmjson.log import create_structured_logger

# 创建结构化日志器
structured_logger = create_structured_logger({'service': 'api'})

# 记录事件
structured_logger.log_event('user_login', {
    'user_id': 'user_123',
    'login_method': 'oauth'
})

# 记录指标
structured_logger.log_metrics({
    'requests_per_second': 100,
    'response_time': 0.5
})

# 记录性能数据
structured_logger.log_performance('api_call', 1.2, {
    'endpoint': '/api/users',
    'method': 'GET'
})
```

### 环境配置

```python
from llmjson.log import setup_environment_logging

# 为不同环境设置日志
logger = setup_environment_logging("production")  # 或 "development", "testing"
```

### 从配置文件加载

```python
from llmjson.log import setup_from_config_file

# 从JSON配置文件加载
logger = setup_from_config_file("logging_config.json")
```

### 装饰器使用

```python
from llmjson.log import log_function_call, log_execution_time

@log_function_call()
def my_function(x, y):
    return x + y

@log_execution_time()
def slow_function():
    import time
    time.sleep(2)
    return "completed"
```

## 配置选项

### LogConfig 类参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `log_level` | str | "INFO" | 日志级别 |
| `log_dir` | str | "logs" | 日志目录 |
| `max_file_size` | int | 50MB | 最大文件大小 |
| `backup_count` | int | 10 | 备份文件数量 |
| `max_days` | int | 30 | 最大保存天数 |
| `enable_console` | bool | True | 启用控制台输出 |
| `enable_file` | bool | True | 启用文件输出 |
| `enable_json` | bool | False | 启用JSON格式 |
| `separate_error_log` | bool | True | 错误日志单独文件 |
| `auto_cleanup` | bool | True | 自动清理旧日志 |
| `enable_async` | bool | False | 启用异步日志 |

### 环境配置

#### Development (开发环境)
- 日志级别: DEBUG
- 控制台输出: 启用
- 异步日志: 禁用
- JSON格式: 禁用
- 保存天数: 7天

#### Testing (测试环境)
- 日志级别: WARNING
- 控制台输出: 禁用
- JSON格式: 启用
- 保存天数: 3天

#### Production (生产环境)
- 日志级别: INFO
- 控制台输出: 禁用
- 异步日志: 启用
- JSON格式: 启用
- 最大文件大小: 100MB
- 备份文件数: 20
- 保存天数: 90天

## 测试和演示

### 运行快速测试
```bash
python test_new_logging.py
```

### 运行完整演示
```bash
python new_logging_demo.py
```

演示脚本包括以下功能展示：
- ✅ 基本日志功能
- ✅ 自定义配置
- ✅ 上下文日志
- ✅ 计时日志
- ✅ 结构化日志
- ✅ 环境配置
- ✅ 装饰器功能
- ✅ 线程安全性
- ✅ JSON格式日志
- ✅ 配置文件使用
- ✅ 错误处理

## 最佳实践

### 1. 使用单例模式
在应用启动时设置一次日志配置，其他地方使用 `get_logger()` 获取日志器实例。

### 2. 合理设置日志级别
- 开发环境：DEBUG
- 测试环境：WARNING
- 生产环境：INFO

### 3. 使用上下文日志
为不同的操作或用户会话添加上下文信息，便于追踪和调试。

### 4. 结构化日志
在需要机器处理或分析的场景下使用结构化日志。

### 5. 性能考虑
- 在高频操作中避免过多的日志输出
- 生产环境可考虑启用异步日志
- 合理设置日志轮转参数

## 故障排除

### 导入错误
确保模块路径正确，所有依赖文件都存在。

### 权限问题
确保对日志目录有写权限。

### 配置文件错误
检查JSON配置文件格式是否正确。

### 线程安全问题
使用单例模式确保线程安全，避免重复初始化。

## 版本信息

- 版本: 2.0
- 更新日期: 2025年9月8日
- 兼容性: Python 3.6+

## 更新日志

### v2.0
- 重构为独立的日志模块
- 添加单例模式支持
- 新增上下文和结构化日志功能
- 支持多种环境配置
- 添加装饰器便捷使用
- 改进线程安全性
- 支持异步日志和JSON格式
