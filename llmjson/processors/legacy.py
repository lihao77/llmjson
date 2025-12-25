"""
兼容性适配器

扩展原有LLMProcessor，添加通用系统支持，同时保持所有原有功能。
"""

from typing import Dict, Any, Optional, List, Tuple
from ..processor import LLMProcessor as OriginalLLMProcessor
from ..templates.legacy import LegacyFloodTemplate
from ..validators.universal import LegacyValidatorAdapter


class EnhancedLLMProcessor(OriginalLLMProcessor):
    """增强版LLMProcessor，在原有功能基础上添加通用系统支持"""
    
    def __init__(self, 
                 api_key: str,
                 base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.1,
                 max_tokens: int = 4000,
                 timeout: int = 60,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 max_workers: int = 4,
                 enable_parallel: bool = True,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 stream: bool = False,
                 force_json: bool = True,
                 extra_body: Optional[Dict[str, Any]] = None,
                 prompt_template: Optional[Any] = None,
                 word_chunker: Optional[Any] = None,
                 # 新增参数：支持通用模板
                 universal_template: Optional[Any] = None,
                 universal_validator: Optional[Any] = None):
        """初始化增强版处理器
        
        保持所有原有参数，同时支持新的通用模板和验证器
        """
        
        # 调用原有的初始化逻辑
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            max_workers=max_workers,
            enable_parallel=enable_parallel,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            stream=stream,
            force_json=force_json,
            extra_body=extra_body,
            prompt_template=prompt_template,
            word_chunker=word_chunker
        )
        
        # 新增：通用系统支持
        self.universal_template = universal_template
        self.universal_validator = universal_validator
        
        # 标记是否使用通用模式
        self.use_universal_mode = universal_template is not None
        
        if self.use_universal_mode:
            self.logger.info("🎯 启用通用模式，使用自定义模板")
        else:
            self.logger.info("🌊 使用传统洪涝灾害模式")
    
    def process_chunk(self, 
                     chunk: str, 
                     doc_name: str = "未知文档") -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """处理文本块
        
        如果配置了通用模板，使用通用处理逻辑；否则使用原有逻辑
        """
        
        if self.use_universal_mode:
            return self._process_chunk_universal(chunk, doc_name)
        else:
            # 使用原有的处理逻辑
            return super().process_chunk(chunk, doc_name)
    
    def _process_chunk_universal(self, chunk: str, doc_name: str) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """使用通用模板处理文本块"""
        
        try:
            # 1. 使用通用模板创建提示
            if self.universal_template:
                prompt = self.universal_template.create_prompt(chunk=chunk, doc_name=doc_name)
            else:
                # 回退到原有逻辑
                prompt = self._create_prompt(chunk, doc_name)
            
            # 2. 调用LLM（复用原有的API调用逻辑）
            reasoning, response = self._call_llm_api(prompt)
            
            # 3. 提取JSON（复用原有逻辑）
            json_data = self._extract_json(response)
            
            if json_data is None:
                return None, {
                    'success': False,
                    'error': 'JSON解析失败',
                    'mode': 'universal'
                }
            
            # 4. 通用验证
            if self.universal_validator:
                json_data, validation_report = self.universal_validator.validate_data(json_data)
            else:
                validation_report = {"validation_skipped": True}
            
            # 5. 添加文档来源（复用原有逻辑）
            self._add_document_source_to_json_data(json_data, doc_name)
            
            return json_data, {
                'success': True,
                'mode': 'universal',
                'validation': validation_report,
                'template_info': self.universal_template.get_template_info() if hasattr(self.universal_template, 'get_template_info') else {}
            }
            
        except Exception as e:
            return None, {
                'success': False,
                'error': str(e),
                'mode': 'universal'
            }
    
    def set_universal_template(self, template, validator=None):
        """动态设置通用模板"""
        self.universal_template = template
        self.universal_validator = validator
        self.use_universal_mode = template is not None
        
        mode = "通用模式" if self.use_universal_mode else "洪涝灾害模式"
        self.logger.info(f"🔄 切换到{mode}")
    
    def get_mode_info(self) -> Dict[str, Any]:
        """获取当前模式信息"""
        return {
            'mode': 'universal' if self.use_universal_mode else 'flood_disaster',
            'template_type': type(self.universal_template).__name__ if self.universal_template else 'PromptTemplate',
            'validator_type': type(self.universal_validator).__name__ if self.universal_validator else 'DataValidator',
            'original_features_available': True
        }


# 为了保持完全兼容，提供一个别名
LegacyProcessorAdapter = EnhancedLLMProcessor