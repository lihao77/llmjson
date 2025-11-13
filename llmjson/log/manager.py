"""
日志管理器

提供单例日志管理器和通用日志管理功能。
"""

import os
import sys
import json
import logging
import logging.handlers
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import LogConfig


class SingletonLogger:
    """单例日志管理器，确保全局只有一个日志实例"""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.logger = None
            self.config = None
            self.log_file_path = None
            self._initialized = True
    
    def setup(self, config: LogConfig, log_file: Optional[str] = None) -> logging.Logger:
        """设置日志系统"""
        if self.logger is not None:
            # 如果已经初始化过，检查是否需要更新日志级别
            if self.config and self.config.log_level != config.log_level:
                # 更新日志级别
                self.logger.setLevel(getattr(logging, config.log_level.upper()))
                # 更新所有处理器的级别
                for handler in self.logger.handlers:
                    handler.setLevel(getattr(logging, config.log_level.upper()))
                self.config.log_level = config.log_level
                print(f"🔄 日志级别已更新为: {config.log_level}")
            return self.logger
        
        self.config = config
        self.logger = logging.getLogger('llmjson')
        self.logger.setLevel(getattr(logging, config.log_level.upper()))
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 设置日志文件路径
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(config.log_dir, exist_ok=True)
            self.log_file_path = os.path.join(config.log_dir, f"llmjson_{timestamp}.log")
        else:
            self.log_file_path = log_file
        
        # 添加处理器
        self._add_console_handler()
        self._add_file_handlers()
        
        # 记录日志系统启动信息
        self._log_startup_info()
        
        return self.logger
    
    def _add_console_handler(self):
        """添加控制台处理器"""
        if not self.config.enable_console:
            return
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.log_level.upper()))
        
        console_formatter = logging.Formatter(self.config.console_format)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def _add_file_handlers(self):
        """添加文件处理器"""
        if not self.config.enable_file:
            return
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        
        # 主日志文件处理器（使用轮转）
        if self.config.enable_async:
            # 异步文件处理器
            from concurrent.futures import ThreadPoolExecutor
            file_handler = AsyncFileHandler(
                self.log_file_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
        else:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
        
        file_handler.setLevel(logging.DEBUG)
        
        if self.config.enable_json:
            file_formatter = JsonFormatter(self.config.json_format)
        else:
            file_formatter = logging.Formatter(self.config.file_format)
        
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # 错误日志单独文件
        if self.config.separate_error_log:
            self._add_error_handler()
    
    def _add_error_handler(self):
        """添加错误日志处理器"""
        error_log_file = self.log_file_path.replace('.log', '_error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        if self.config.enable_json:
            error_formatter = JsonFormatter(self.config.json_format)
        else:
            error_formatter = logging.Formatter(self.config.file_format)
        
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
    
    def _log_startup_info(self):
        """记录日志系统启动信息"""
        self.logger.info("=" * 60)
        self.logger.info("🔧 日志系统初始化完成")
        self.logger.info(f"📄 日志文件: {os.path.abspath(self.log_file_path)}")
        self.logger.info(f"📊 日志级别: {self.config.log_level}")
        self.logger.info(f"💾 最大文件大小: {self.config.max_file_size // 1024 // 1024}MB")
        self.logger.info(f"📦 备份文件数: {self.config.backup_count}")
        if self.config.enable_async:
            self.logger.info("⚡ 异步日志已启用")
        if self.config.enable_json:
            self.logger.info("📋 JSON格式日志已启用")
        self.logger.info("=" * 60)
    
    def get_logger(self) -> Optional[logging.Logger]:
        """获取日志器实例"""
        return self.logger
    
    def cleanup_old_logs(self):
        """清理旧日志文件"""
        if not self.config or not self.config.auto_cleanup:
            return
        
        try:
            log_dir = Path(self.config.log_dir)
            if not log_dir.exists():
                return
            
            cutoff_time = datetime.now().timestamp() - (self.config.max_days * 24 * 3600)
            
            cleaned_files = 0
            for log_file in log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    try:
                        log_file.unlink()
                        cleaned_files += 1
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"无法删除日志文件 {log_file}: {e}")
            
            if cleaned_files > 0 and self.logger:
                self.logger.info(f"🧹 清理了 {cleaned_files} 个过期日志文件")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"清理日志文件时发生错误: {e}")
    
    def reset(self):
        """重置日志管理器（主要用于测试）"""
        if self.logger:
            self.logger.handlers.clear()
        self.logger = None
        self.config = None
        self.log_file_path = None


class LogManager:
    """通用日志管理器（非单例）"""
    
    def __init__(self, config: LogConfig):
        self.config = config
        self.logger = None
    
    def setup_logging(self, logger_name: str = 'llmjson') -> logging.Logger:
        """设置日志系统"""
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 添加处理器
        if self.config.enable_console:
            self._add_console_handler()
        
        if self.config.enable_file:
            self._add_file_handlers()
        
        return self.logger
    
    def _add_console_handler(self):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.log_level.upper()))
        
        console_formatter = logging.Formatter(self.config.console_format)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def _add_file_handlers(self):
        """添加文件处理器"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self.config.log_dir, exist_ok=True)
        log_file_path = os.path.join(self.config.log_dir, f"llmjson_{timestamp}.log")
        
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        # 主日志文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        if self.config.enable_json:
            file_formatter = JsonFormatter(self.config.json_format)
        else:
            file_formatter = logging.Formatter(self.config.file_format)
        
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)


class JsonFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def __init__(self, format_dict):
        super().__init__()
        self.format_dict = format_dict
    
    def format(self, record):
        # 首先调用父类的format来确保record有正确的属性
        self.formatTime(record)  # 确保asctime属性存在
        
        log_entry = {}
        for key, value in self.format_dict.items():
            try:
                # 使用标准的LogRecord格式化
                if isinstance(value, str) and '%(' in value:
                    formatted_value = value % record.__dict__
                else:
                    formatted_value = value
                log_entry[key] = formatted_value
            except (KeyError, ValueError, TypeError):
                # 如果格式化失败，尝试直接从record获取属性
                if key == 'timestamp':
                    log_entry[key] = self.formatTime(record)
                elif key == 'message':
                    log_entry[key] = record.getMessage()
                elif key == 'level':
                    log_entry[key] = record.levelname
                elif key == 'filename':
                    log_entry[key] = record.filename
                elif key == 'lineno':
                    log_entry[key] = record.lineno
                elif key == 'name':
                    log_entry[key] = record.name
                else:
                    log_entry[key] = str(value)
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class AsyncFileHandler(logging.handlers.RotatingFileHandler):
    """异步文件处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from concurrent.futures import ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="AsyncLogger")
    
    def emit(self, record):
        """异步发出日志记录"""
        self.executor.submit(super().emit, record)
    
    def close(self):
        """关闭处理器"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
        super().close()
