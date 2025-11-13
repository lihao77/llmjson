"""配置管理

提供LLM处理器和相关组件的配置管理功能。
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from .exceptions import ValidationError


@dataclass
class LLMConfig:
    """LLM配置类"""
    api_key: str = "placeholder-key"
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    stream: bool = False
    force_json: bool = True
    extra_body: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初始化后验证"""
        self.validate()
    
    def validate(self):
        """验证配置参数"""
        if not self.api_key:
            raise ValidationError("API密钥不能为空")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValidationError("temperature必须在0-2之间")
        
        if self.max_tokens <= 0:
            raise ValidationError("max_tokens必须大于0")
        
        if self.timeout <= 0:
            raise ValidationError("timeout必须大于0")
        
        if self.max_retries < 0:
            raise ValidationError("max_retries不能小于0")
        
        if self.retry_delay < 0:
            raise ValidationError("retry_delay不能小于0")


@dataclass
class ProcessingConfig:
    """处理配置类"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_workers: int = 4
    enable_parallel: bool = True
    
    def __post_init__(self):
        """初始化后验证"""
        self.validate()
    
    def validate(self):
        """验证配置参数"""
        if self.chunk_size <= 0:
            raise ValidationError("chunk_size必须大于0")
        
        if self.chunk_overlap < 0:
            raise ValidationError("chunk_overlap不能小于0")
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValidationError("chunk_overlap必须小于chunk_size")
        
        if self.max_workers <= 0:
            raise ValidationError("max_workers必须大于0")



class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        # # 创建配置时提供默认API密钥以通过验证
        # self.llm_config = LLMConfig(api_key="placeholder-key")
        self.llm_config = LLMConfig()
        self.processing_config = ProcessingConfig()
        
        # 如果提供了配置文件，则加载配置
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        else:
            # 尝试从环境变量加载
            self.load_from_env()
    
    def load_from_file(self, config_file: str):
        """从文件加载配置
        
        Args:
            config_file: 配置文件路径
            
        Raises:
            ValidationError: 当配置文件格式错误时
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 加载LLM配置
            if 'llm' in config_data:
                llm_data = config_data['llm']
                self.llm_config = LLMConfig(**llm_data)
            
            # 加载处理配置
            if 'processing' in config_data:
                processing_data = config_data['processing']
                self.processing_config = ProcessingConfig(**processing_data)
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"配置文件JSON格式错误: {str(e)}")
        except Exception as e:
            raise ValidationError(f"加载配置文件失败: {str(e)}")
    
    def load_from_env(self):
        """从环境变量加载配置"""
        # LLM配置
        if os.getenv('OPENAI_API_KEY'):
            self.llm_config.api_key = os.getenv('OPENAI_API_KEY')
        
        if os.getenv('OPENAI_BASE_URL'):
            self.llm_config.base_url = os.getenv('OPENAI_BASE_URL')
        
        if os.getenv('OPENAI_MODEL'):
            self.llm_config.model = os.getenv('OPENAI_MODEL')
        
        if os.getenv('LLM_TEMPERATURE'):
            try:
                self.llm_config.temperature = float(os.getenv('LLM_TEMPERATURE'))
            except ValueError:
                pass
        
        if os.getenv('LLM_MAX_TOKENS'):
            try:
                self.llm_config.max_tokens = int(os.getenv('LLM_MAX_TOKENS'))
            except ValueError:
                pass
        
        # 处理配置
        if os.getenv('CHUNK_SIZE'):
            try:
                self.processing_config.chunk_size = int(os.getenv('CHUNK_SIZE'))
            except ValueError:
                pass
        
        if os.getenv('CHUNK_OVERLAP'):
            try:
                self.processing_config.chunk_overlap = int(os.getenv('CHUNK_OVERLAP'))
            except ValueError:
                pass
        
        if os.getenv('MAX_WORKERS'):
            try:
                self.processing_config.max_workers = int(os.getenv('MAX_WORKERS'))
            except ValueError:
                pass
    
    def save_to_file(self, config_file: str):
        """保存配置到文件
        
        Args:
            config_file: 配置文件路径
            
        Raises:
            ValidationError: 当保存失败时
        """
        try:
            config_data = {
                'llm': asdict(self.llm_config),
                'processing': asdict(self.processing_config),
            }
            
            # 移除敏感信息（API密钥）
            if 'api_key' in config_data['llm']:
                config_data['llm']['api_key'] = "YOUR_API_KEY_HERE"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise ValidationError(f"保存配置文件失败: {str(e)}")
    
    def update_llm_config(self, **kwargs):
        """更新LLM配置
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if hasattr(self.llm_config, key):
                setattr(self.llm_config, key, value)
        
        # 重新验证
        self.llm_config.validate()
    
    def update_processing_config(self, **kwargs):
        """更新处理配置
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if hasattr(self.processing_config, key):
                setattr(self.processing_config, key, value)
        
        # 重新验证
        self.processing_config.validate()
    
    def get_llm_config_dict(self) -> Dict[str, Any]:
        """获取LLM配置字典
        
        Returns:
            LLM配置字典
        """
        return asdict(self.llm_config)
    
    def get_processing_config_dict(self) -> Dict[str, Any]:
        """获取处理配置字典
        
        Returns:
            处理配置字典
        """
        return asdict(self.processing_config)
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置
        
        Returns:
            完整配置字典
        """
        return {
            'llm': self.get_llm_config_dict(),
            'processing': self.get_processing_config_dict()
        }
    
    def get_merged_config(self) -> Dict[str, Any]:
        """获取合并后的配置，用于直接传递给LLM处理器
        
        Returns:
            合并后的配置字典，包含LLM配置和处理配置的所有参数
        """
        llm_config = self.get_llm_config_dict()
        processing_config = self.get_processing_config_dict()
        
        # 将处理配置合并到LLM配置中
        merged_config = llm_config.copy()
        merged_config.update({
            'max_workers': processing_config.get('max_workers', 4),
            'enable_parallel': processing_config.get('enable_parallel', True),
            'chunk_size': processing_config.get('chunk_size', 2000),
            'chunk_overlap': processing_config.get('chunk_overlap', 200),
        })
        
        return merged_config
    
    def validate_all(self):
        """验证所有配置
        
        Raises:
            ValidationError: 当配置无效时
        """
        self.llm_config.validate()
        self.processing_config.validate()
    
    def create_sample_config(self, output_file: str):
        """创建示例配置文件
        
        Args:
            output_file: 输出文件路径
        """
        sample_config = {
            "llm": {
                "api_key": "YOUR_API_KEY_HERE",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 4000,
                "timeout": 60,
                "max_retries": 3,
                "retry_delay": 1.0
            },
            "processing": {
                "chunk_size": 3000,
                "chunk_overlap": 200,
                "max_workers": 4,
                "enable_parallel": True
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ValidationError(f"创建示例配置文件失败: {str(e)}")


def load_config(config_file: Optional[str] = None) -> ConfigManager:
    """加载配置
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置管理器实例
    """
    return ConfigManager(config_file)


def create_default_config() -> ConfigManager:
    """创建默认配置
    
    Returns:
        默认配置管理器实例
    """
    return ConfigManager()