"""LLMJSON包

一个简洁高效的用于大语言模型生成JSON数据的Python包。

版本2.0新增：
- 通用化信息抽取框架
- 配置驱动的模板系统
- 插件化验证规则
- 完全向后兼容
"""

__version__ = "2.0.0"
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

# 原有核心模块（继续使用，保持完全兼容）
from .processor import LLMProcessor
from .validator import DataValidator
from .prompt_template import PromptTemplate

# 新的通用系统
from .processors.universal import UniversalProcessor
from .templates.base import ConfigurableTemplate, BaseTemplate
from .templates.legacy import LegacyFloodTemplate
from .validators.universal import UniversalValidator
from .validators.base import BaseValidator
from .factory import ProcessorFactory, TemplateFactory

# 兼容性适配器（作为可选的增强版本）
from .processors.legacy import EnhancedLLMProcessor, LegacyProcessorAdapter

# 提供选择：用户可以选择使用原版还是增强版
# 默认使用原版以保持完全兼容
# LLMProcessor = LLMProcessor  # 使用原版（默认）
# 如果用户想要增强功能，可以：
# from llmjson import EnhancedLLMProcessor as LLMProcessor
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
    
    # 兼容接口（继续使用原有实现）
    'LLMProcessor',           # 原有的LLMProcessor，保持所有功能
    'DataValidator',          # 原有的DataValidator
    'PromptTemplate',         # 原有的PromptTemplate
    'DocumentProcessor',
    
    # 增强接口（可选使用）
    'EnhancedLLMProcessor',   # 增强版LLMProcessor，支持通用模板
    'LegacyProcessorAdapter', # 完全基于新系统的适配器
    
    # 新的通用接口（推荐新项目使用）
    'UniversalProcessor',
    'ConfigurableTemplate',
    'BaseTemplate',
    'LegacyFloodTemplate',
    'UniversalValidator',
    'BaseValidator',
    'ProcessorFactory',
    'TemplateFactory',
    
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

# 兼容性和迁移提示
def show_migration_guide():
    """显示迁移指南"""
    print("""
🎉 LLMJson 2.0 - 通用化信息抽取框架

✨ 新功能：
  • 支持任意领域的信息抽取
  • 配置驱动的模板系统  
  • 插件化验证规则
  • 完全向后兼容

🚀 快速开始：

# 方式1：继续使用原有系统（推荐，零风险）
from llmjson import LLMProcessor  # 使用原有的完整实现
processor = LLMProcessor(api_key="your-key")
result, info = processor.process_chunk(text, 'doc.txt')

# 方式2：使用增强版（原有功能 + 通用支持）
from llmjson import EnhancedLLMProcessor
processor = EnhancedLLMProcessor(api_key="your-key")  # 默认洪涝灾害模式
# 可选：切换到通用模式
from llmjson import ConfigurableTemplate
template = ConfigurableTemplate('templates/knowledge_graph.yaml')
processor.set_universal_template(template)

# 方式3：使用全新的通用系统
from llmjson import ProcessorFactory
processor = ProcessorFactory.create_processor('config.json')
result, info = processor.process_chunk(text, 'doc.txt')

📚 详细文档和示例：
  • 设计文档：llmjson_universal_design.md
  • 迁移指南：migration_guide.md
  • 使用演示：demo_universal_usage.py
""")

# 可选：在首次导入时显示提示
import os
if os.getenv('LLMJSON_SHOW_MIGRATION_GUIDE', '').lower() in ('1', 'true', 'yes'):
    show_migration_guide()