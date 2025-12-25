"""
LLMJson - 基于大语言模型的知识图谱提取工具

v2.0 - 配置驱动的通用信息提取系统
"""

from .factory import ProcessorFactory, TemplateFactory
from .processors.universal import UniversalProcessor
from .templates.base import ConfigurableTemplate
from .validators.universal import UniversalValidator
from .exceptions import LLMProcessingError, ValidationError, APIConnectionError

__version__ = "2.0.0"
__author__ = "LLMJson Team"

# 主要导出
__all__ = [
    # 工厂类
    "ProcessorFactory",
    "TemplateFactory",
    
    # 核心处理器
    "UniversalProcessor",
    
    # 模板和验证器
    "ConfigurableTemplate", 
    "UniversalValidator",
    
    # 异常类
    "LLMProcessingError",
    "ValidationError", 
    "APIConnectionError"
]
