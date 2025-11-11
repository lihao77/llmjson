"""
日志设置和便捷函数

提供日志系统的设置和常用函数。
"""

import logging
from typing import Optional, Dict, Any

from .config import LogConfig, EnvironmentLogConfig
from .manager import SingletonLogger, LogManager
from .context import ContextLogger, TimedContextLogger, StructuredLogger


def setup_logging(
    log_level: str = "INFO", 
    log_file: Optional[str] = None, 
    config: Optional[LogConfig] = None,
    use_singleton: bool = True
) -> logging.Logger:
    """设置日志记录（优化版本）
    
    Args:
        log_level: 日志级别
        log_file: 日志文件路径，如果为None则自动生成
        config: 日志配置对象
        use_singleton: 是否使用单例模式
        
    Returns:
        配置好的日志记录器
    """
    # 使用默认配置或提供的配置
    if config is None:
        config = LogConfig()
        config.log_level = log_level
    
    if use_singleton:
        # 使用单例模式确保全局唯一的日志实例
        singleton_logger = SingletonLogger()
        logger = singleton_logger.setup(config, log_file)
        
        # 清理旧日志文件
        singleton_logger.cleanup_old_logs()
    else:
        # 使用普通日志管理器
        log_manager = LogManager(config)
        logger = log_manager.setup_logging()

    return logger


def get_logger(name: str = 'llm_json_generator') -> logging.Logger:
    """获取日志器实例（推荐使用）
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    singleton_logger = SingletonLogger()
    logger = singleton_logger.get_logger()
    
    if logger is None:
        # 如果还没有初始化，使用默认配置初始化
        return setup_logging()
    
    return logger


def create_logger_with_context(context: Dict[str, Any]) -> ContextLogger:
    """创建带上下文信息的日志器
    
    Args:
        context: 上下文信息字典
        
    Returns:
        上下文日志器
    """
    logger = get_logger()
    return ContextLogger(logger, context)


def create_timed_logger(context: Dict[str, Any]) -> TimedContextLogger:
    """创建带时间统计的上下文日志器
    
    Args:
        context: 上下文信息字典
        
    Returns:
        带时间统计的上下文日志器
    """
    logger = get_logger()
    return TimedContextLogger(logger, context)


def create_structured_logger(context: Dict[str, Any]) -> StructuredLogger:
    """创建结构化日志器
    
    Args:
        context: 上下文信息字典
        
    Returns:
        结构化日志器
    """
    logger = get_logger()
    return StructuredLogger(logger, context)


def setup_environment_logging(environment: str = "development") -> logging.Logger:
    """设置环境相关的日志配置
    
    Args:
        environment: 环境名称 (development, testing, production)
        
    Returns:
        配置好的日志记录器
    """
    env_config = EnvironmentLogConfig(environment)
    config = env_config.get_config()
    
    return setup_logging(config=config)


def setup_from_config_file(config_file: str) -> logging.Logger:
    """从配置文件设置日志
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置好的日志记录器
    """
    config = LogConfig.from_json_file(config_file)
    return setup_logging(config=config)


def reset_logging():
    """重置日志系统（主要用于测试）"""
    singleton_logger = SingletonLogger()
    singleton_logger.reset()


def log_system_info():
    """记录系统信息"""
    import sys
    import platform
    
    logger = get_logger()
    
    logger.info("=" * 60)
    logger.info("💻 系统信息")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"操作系统: {platform.system()} {platform.release()}")
    logger.info(f"处理器: {platform.processor()}")
    logger.info("=" * 60)


# 便捷的日志装饰器
def log_function_call(logger_name: str = None):
    """函数调用日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name) if logger_name else get_logger()
            
            logger.info(f"🔧 调用函数: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"✅ 函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"❌ 函数 {func.__name__} 执行失败: {e}")
                raise
        
        return wrapper
    return decorator


def log_execution_time(logger_name: str = None):
    """执行时间日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            logger = get_logger(logger_name) if logger_name else get_logger()
            
            start_time = time.time()
            logger.info(f"⏱️ 开始执行: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                duration = end_time - start_time
                logger.info(f"✅ 执行完成: {func.__name__}, 耗时: {duration:.2f}秒")
                return result
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                logger.error(f"❌ 执行失败: {func.__name__}, 耗时: {duration:.2f}秒, 错误: {e}")
                raise
        
        return wrapper
    return decorator
