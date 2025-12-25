"""
通用处理器

基于模板和验证器的通用信息抽取处理器。
"""

from typing import Dict, Any, Optional, List, Tuple
import time
import json
import re
import jsonschema
from openai import OpenAI
import json_repair

from ..templates.base import BaseTemplate
from ..validators.base import BaseValidator
from ..log import create_logger_with_context, log_execution_time
from ..exceptions import LLMProcessingError, APIConnectionError


class UniversalProcessor:
    """通用处理器，支持任意领域的信息抽取"""
    
    def __init__(self, 
                 template: BaseTemplate,
                 validator: Optional[BaseValidator] = None,
                 api_key: str = None,
                 base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-4o-mini",
                 temperature: float = 0.1,
                 max_tokens: int = 4000,
                 timeout: int = 60,
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 **kwargs):
        """初始化通用处理器
        
        Args:
            template: 模板实例
            validator: 验证器实例（可选）
            api_key: OpenAI API密钥
            base_url: API基础URL
            model: 使用的模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间（秒）
            **kwargs: 其他参数
        """
        
        # 创建上下文日志器
        self.logger = create_logger_with_context({
            'component': 'UniversalProcessor',
            'model': model,
            'template': template.__class__.__name__
        })
        
        self.template = template
        self.validator = validator
        
        # LLM配置
        if api_key:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = None
            self.logger.warning("未提供API密钥，将无法调用LLM")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0,
            'json_parsing_errors': 0
        }
    
    @log_execution_time()
    def process_chunk(self, chunk: str, doc_name: str = "未知文档") -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """处理文本块，生成结构化数据
        
        Args:
            chunk: 待处理的文本块
            doc_name: 文档名称
            
        Returns:
            (处理结果, 处理信息)
            
        Raises:
            LLMProcessingError: 当处理失败时
        """
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        # 创建处理特定的日志器
        process_logger = create_logger_with_context({
            'operation': 'process_chunk',
            'doc_name': doc_name
        })
        
        try:
            process_logger.debug(f"🔄 开始处理文档块，长度: {len(chunk)} 字符")
            
            # 1. 创建提示
            prompt = self.template.create_prompt(chunk=chunk, doc_name=doc_name)
            process_logger.debug(f"📝 提示创建完成，消息数: {len(prompt)}")
            
            # 2. 调用LLM API
            if not self.client:
                raise LLMProcessingError("未配置LLM客户端")
            
            response = self._call_llm_api(prompt)
            process_logger.debug(f"📡 API调用完成，响应长度: {len(response) if response else 0} 字符")
            
            # 3. 提取JSON数据
            json_data = self._extract_json(response)
            if json_data is None:
                self.stats['json_parsing_errors'] += 1
                self.stats['failed_requests'] += 1
                
                error_details = {
                    'success': False,
                    'error': 'JSON解析失败',
                    'error_type': 'json_parse_error',
                    'raw_response': response[:1000] if response else None,
                    'processing_time': time.time() - start_time,
                    'chunk_length': len(chunk)
                }
                
                process_logger.error(f"❌ JSON解析失败")
                return None, error_details
            
            # 4. 模板验证
            try:
                jsonschema.validate(json_data, self.template.schema)
                process_logger.debug(f"✅ 模板验证通过")
            except jsonschema.ValidationError as e:
                self.stats['failed_requests'] += 1
                error_details = {
                    'success': False,
                    'error': '输出格式不符合模板要求',
                    'error_type': 'template_validation_error',
                    'validation_error': str(e),
                    'validation_path': list(e.absolute_path) if e.absolute_path else [],
                    'failed_value': e.instance,
                    'schema_path': list(e.schema_path) if e.schema_path else [],
                    'raw_output': response[:2000] if response else None,
                    'processing_time': time.time() - start_time
                }
                process_logger.error(f"❌ 模板验证失败: {str(e)}")
                process_logger.error(f"   验证路径: {error_details['validation_path']}")
                process_logger.error(f"   失败值: {error_details['failed_value']}")
                return None, error_details
            
            # 5. 数据验证和修正
            validation_result = {"validation_skipped": True}
            if self.validator:
                json_data, validation_result = self.validator.validate_data(json_data)
                process_logger.debug(f"✅ 数据验证完成")
            
            # 6. 添加文档来源
            self._add_document_source(json_data, doc_name)
            
            processing_time = time.time() - start_time
            self.stats['successful_requests'] += 1
            
            success_details = {
                'success': True,
                'model': self.model,
                'chunk_length': len(chunk),
                'response_length': len(response) if response else 0,
                'processing_time': processing_time,
                'validation': validation_result,
                'template_info': self.template.get_template_info() if hasattr(self.template, 'get_template_info') else {}
            }
            
            process_logger.info(f"✅ 处理成功，耗时: {processing_time:.2f}s")
            
            return json_data, success_details
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats['failed_requests'] += 1
            error_msg = f"处理文本块失败: {str(e)}"
            
            process_logger.error(f"❌ {error_msg}")
            
            raise LLMProcessingError(error_msg) from e
    
    def _call_llm_api(self, prompt: List[Dict[str, str]]) -> str:
        """调用LLM API
        
        Args:
            prompt: messages 列表
            
        Returns:
            LLM响应文本
            
        Raises:
            APIConnectionError: 当API调用失败时
        """
        # 创建API调用特定的上下文日志器
        api_logger = create_logger_with_context({
            'operation': 'api_call',
        })
        
        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "response_format": {"type": "json_object"}
        }
        
        # 重试机制
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                api_logger.info(f"📡 开始API调用 (尝试 {attempt + 1}/{self.max_retries})")
                
                response = self.client.chat.completions.create(**request_params)
                
                # 记录响应信息
                if hasattr(response, 'usage') and response.usage:
                    self.stats['total_tokens_used'] += response.usage.total_tokens
                    api_logger.info(f"✅ API调用成功!")
                    api_logger.info(f"  📥 输入Token: {response.usage.prompt_tokens}")
                    api_logger.info(f"  📤 输出Token: {response.usage.completion_tokens}")
                    api_logger.info(f"  📊 总Token: {response.usage.total_tokens}")
                
                response_content = response.choices[0].message.content
                api_logger.info(f"  📏 响应长度: {len(response_content) if response_content else 0} 字符")
                
                return response_content
                    
            except Exception as e:
                last_exception = e
                api_logger.warning(f"⚠️ API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                
                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (2 ** attempt)
                    api_logger.info(f"⏳ 等待 {sleep_time:.1f} 秒后重试...")
                    time.sleep(sleep_time)
                    continue
                else:
                    break
        
        # 所有重试都失败了
        error_msg = f"API调用失败，已重试{self.max_retries}次: {str(last_exception)}"
        api_logger.error(f"❌ {error_msg}")
        raise APIConnectionError(error_msg) from last_exception
    
    def _extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """从LLM响应中提取JSON数据
        
        Args:
            response: LLM响应文本
            
        Returns:
            解析后的JSON数据，失败时返回None
        """
        if not response:
            return None
        
        # 创建JSON提取特定的日志器
        extract_logger = create_logger_with_context({
            'operation': 'json_extraction'
        })
        
        extract_logger.debug(f"🔍 开始JSON提取，响应长度: {len(response)} 字符")
        
        # 1. 首先尝试直接解析
        try:
            result = json.loads(response)
            extract_logger.info("✅ 直接JSON解析成功")
            return result
        except json.JSONDecodeError as e:
            extract_logger.debug(f"❌ 直接JSON解析失败: {str(e)}")
        
        # 2. 尝试提取JSON代码块
        extract_logger.debug("🔍 尝试提取JSON代码块...")
        json_patterns = [
            r'```(?:json)?\s*({.*?})\s*```',  # 标准代码块
            r'```(?:json)?\s*(\[.*?\])\s*```'  # 数组代码块
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for i, match in enumerate(matches):
                try:
                    result = json.loads(match)
                    extract_logger.info(f"✅ JSON代码块解析成功 (第{i+1}个)")
                    return result
                except json.JSONDecodeError:
                    continue
        
        # 3. 智能查找JSON对象
        extract_logger.debug("🔍 尝试智能JSON对象提取...")
        json_candidates = self._find_json_candidates(response)
        
        for i, candidate in enumerate(json_candidates):
            try:
                result = json.loads(candidate)
                extract_logger.info(f"✅ JSON对象解析成功 (候选项{i+1})")
                return result
            except json.JSONDecodeError:
                continue
        
        # 4. 使用json_repair尝试修复
        extract_logger.debug("🔧 尝试JSON修复...")
        try:
            repaired = json_repair.repair_json(response)
            result = json.loads(repaired)
            extract_logger.info(f"✅ JSON修复成功")
            return result
        except Exception as e:
            extract_logger.debug(f"❌ JSON修复失败: {str(e)}")
        
        extract_logger.error("❌ 所有JSON提取方法都失败了")
        return None
    
    def _find_json_candidates(self, text: str) -> List[str]:
        """智能查找JSON候选项"""
        candidates = []
        
        # 查找完整的大括号包围的内容
        brace_count = 0
        start_pos = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_pos = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_pos != -1:
                    candidate = text[start_pos:i + 1]
                    if len(candidate) > 10:  # 过滤太短的内容
                        candidates.append(candidate)
                    start_pos = -1
        
        return candidates[:5]  # 限制候选项数量
    
    def _add_document_source(self, json_data: Dict[str, Any], doc_name: str) -> None:
        """为JSON数据添加文档来源信息"""
        if not isinstance(json_data, dict):
            return
        
        # 递归添加文档来源
        def add_source_recursive(obj, source):
            if isinstance(obj, dict):
                obj["文档来源"] = source
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        add_source_recursive(value, source)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        add_source_recursive(item, source)
        
        # 为顶级数组添加来源
        for key, value in json_data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        item["文档来源"] = doc_name
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        stats = self.stats.copy()
        
        # 计算成功率
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_requests'] / stats['total_requests'] * 100
        else:
            stats['success_rate'] = 0.0
        
        # 计算平均token使用量
        if stats['successful_requests'] > 0:
            stats['avg_tokens_per_request'] = stats['total_tokens_used'] / stats['successful_requests']
        else:
            stats['avg_tokens_per_request'] = 0.0
        
        return stats