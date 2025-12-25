"""
日志配置类

定义日志系统的各种配置选项。
"""

from typing import Dict, Any
import os


class LogConfig:
    """日志配置类"""
    
    def __init__(self):
        # 基础配置
        self.log_level = "INFO"
        self.log_dir = "logs"
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.backup_count = 10
        self.max_days = 30
        
        # 功能开关
        self.enable_console = True
        self.enable_file = True
        self.enable_json = False
        self.separate_error_log = True
        self.auto_cleanup = True
        self.enable_async = False
        
        # 格式配置
        self.console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.file_format = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        self.json_format = {
            "timestamp": "%(asctime)s",
            "name": "%(name)s",
            "level": "%(levelname)s",
            "filename": "%(filename)s",
            "lineno": "%(lineno)d",
            "message": "%(message)s"
        }
        
        # 性能配置
        self.buffer_size = 1024  # 缓冲区大小
        self.flush_interval = 5  # 刷新间隔（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'log_level': self.log_level,
            'log_dir': self.log_dir,
            'max_file_size': self.max_file_size,
            'backup_count': self.backup_count,
            'max_days': self.max_days,
            'enable_console': self.enable_console,
            'enable_file': self.enable_file,
            'enable_json': self.enable_json,
            'separate_error_log': self.separate_error_log,
            'auto_cleanup': self.auto_cleanup,
            'enable_async': self.enable_async,
            'console_format': self.console_format,
            'file_format': self.file_format,
            'json_format': self.json_format,
            'buffer_size': self.buffer_size,
            'flush_interval': self.flush_interval
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogConfig':
        """从字典创建配置"""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
    
    @classmethod
    def from_json_file(cls, file_path: str) -> 'LogConfig':
        """从JSON文件加载配置"""
        import json
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 如果是嵌套的配置结构，提取logging部分
        if 'logging' in data:
            data = data['logging']
        
        return cls.from_dict(data)
    
    def save_to_json_file(self, file_path: str):
        """保存配置到JSON文件"""
        import json
        file_path = os.path.abspath(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'logging': self.to_dict()}, f, indent=2, ensure_ascii=False)


class EnvironmentLogConfig:
    """环境相关的日志配置"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment.lower()
    
    def get_config(self) -> LogConfig:
        """根据环境获取配置"""
        config = LogConfig()
        
        if self.environment == "development":
            config.log_level = "DEBUG"
            config.enable_console = True
            config.enable_file = True
            config.enable_json = False
            
        elif self.environment == "testing":
            config.log_level = "INFO"
            config.enable_console = False
            config.enable_file = True
            config.enable_json = True
            
        elif self.environment == "production":
            config.log_level = "WARNING"
            config.enable_console = False
            config.enable_file = True
            config.enable_json = True
            config.auto_cleanup = True
            
        else:
            # 默认配置
            config.log_level = "INFO"
        
        return config
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"无效的日志级别: {self.log_level}")
        
        if self.max_file_size <= 0:
            raise ValueError(f"无效的最大文件大小: {self.max_file_size}")
        
        if self.backup_count < 0:
            raise ValueError(f"无效的备份文件数: {self.backup_count}")
        
        if self.max_days <= 0:
            raise ValueError(f"无效的最大保存天数: {self.max_days}")
        
        return True
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"LogConfig(level={self.log_level}, dir={self.log_dir}, max_size={self.max_file_size//1024//1024}MB)"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"LogConfig({self.to_dict()})"


class EnvironmentLogConfig:
    """环境相关的日志配置"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.configs = {
            "development": self._get_development_config(),
            "testing": self._get_testing_config(),
            "production": self._get_production_config()
        }
    
    def _get_development_config(self) -> LogConfig:
        """开发环境配置"""
        config = LogConfig()
        config.log_level = "DEBUG"
        config.enable_console = True
        config.enable_async = False
        config.enable_json = False
        config.max_days = 7
        return config
    
    def _get_testing_config(self) -> LogConfig:
        """测试环境配置"""
        config = LogConfig()
        config.log_level = "INFO"  # 修复：降低日志级别以显示INFO消息
        config.enable_console = True  # 修复：启用控制台输出以便演示
        config.enable_json = True
        config.max_days = 3
        return config
    
    def _get_production_config(self) -> LogConfig:
        """生产环境配置"""
        config = LogConfig()
        config.log_level = "INFO"
        config.enable_console = False
        config.enable_async = True
        config.enable_json = True
        config.max_file_size = 100 * 1024 * 1024  # 100MB
        config.backup_count = 20
        config.max_days = 90
        return config
    
    def get_config(self, environment: str = None) -> LogConfig:
        """获取指定环境的配置"""
        env = environment or self.environment
        
        if env not in self.configs:
            raise ValueError(f"不支持的环境: {env}. 支持的环境: {list(self.configs.keys())}")
        
        return self.configs[env]
