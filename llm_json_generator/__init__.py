"""LLM JSON生成器包

一个用于大语言模型生成JSON数据的标准Python包。
"""

__version__ = "1.0.0"
__author__ = "Knowledge Graph Team"
__email__ = "team@example.com"

# 导入主要模块
from .exceptions import (
    LLMProcessingError,
    ValidationError,
    APIConnectionError,
    JSONParsingError,
    PromptTemplateError
)

from .processor import LLMProcessor
from .validator import DataValidator
from .prompt_template import PromptTemplate
from .config import (
    ConfigManager,
    LLMConfig,
    ProcessingConfig,
    load_config,
    create_default_config
)
from .log import (
    LogConfig,
    SingletonLogger,
    LogManager,
    ContextLogger,
    setup_logging,
    get_logger,
    create_logger_with_context,
    create_timed_logger,
    create_structured_logger,
    setup_environment_logging,
    setup_from_config_file
)
from .utils import (
    ensure_dir,
    save_json,
    load_json,
    sanitize_filename,
    chunk_text,
    Timer,
    merge_knowledge_graph_results
)

from .word_chunker import (
    WordChunker,
    chunk_word_document,
    extract_text_from_word
)

from .run_mode import DocumentProcessor

# CLI模块（可选导入）
try:
    from . import cli
except ImportError:
    cli = None

# 定义公开的API
__all__ = [
    # 异常类
    'LLMProcessingError',
    'ValidationError', 
    'APIConnectionError',
    'JSONParsingError',
    'PromptTemplateError',
    
    # 核心类
    'LLMProcessor',
    'DataValidator',
    'PromptTemplate',
    'DocumentProcessor',
    
    # 配置相关
    'ConfigManager',
    'LLMConfig',
    'ProcessingConfig', 
    'load_config',
    'create_default_config',
    
    # 日志相关
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
    
    # 工具函数
    'ensure_dir',
    'save_json',
    'load_json',
    'sanitize_filename',
    'chunk_text',
    'Timer',
    'merge_knowledge_graph_results',
    
    # Word文档处理
    'WordChunker',
    'chunk_word_document',
    'extract_text_from_word'
]