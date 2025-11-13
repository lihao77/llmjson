"""
日志模块

提供完整的日志管理功能，包括配置、单例管理器和上下文日志器。
"""

from .config import LogConfig
from .manager import SingletonLogger, LogManager
from .context import ContextLogger
from .setup import (
    setup_logging, 
    get_logger, 
    create_logger_with_context, 
    create_timed_logger, 
    create_structured_logger, 
    setup_environment_logging, 
    setup_from_config_file,
    log_function_call,
    log_execution_time,
    log_system_info
)

__all__ = [
    'LogConfig',
    'SingletonLogger',
    'LogManager',
    'ContextLogger',
    'setup_logging',
    'get_logger',
    'create_logger_with_context',
    'create_timed_logger',
    'create_structured_logger',
    'setup_environment_logging',
    'setup_from_config_file',
    'log_function_call',
    'log_execution_time',
    'log_system_info'
]
