"""LLM处理器

提供大语言模型调用和JSON数据生成功能。
"""

import json
import os
import re
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from openai import OpenAI
import json_repair
from concurrent.futures import ThreadPoolExecutor, as_completed

from .prompt_template import PromptTemplate
from .word_chunker import WordChunker
from .log import (
    setup_logging,
    get_logger,
    create_logger_with_context,
    create_timed_logger,
    log_execution_time,
    log_system_info
)
from .exceptions import (
    LLMProcessingError, 
    APIConnectionError, 
    ValidationError
)


class LLMProcessor:
    """大语言模型处理器"""
    
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
                 prompt_template: Optional[PromptTemplate] = None,
                 word_chunker: Optional[WordChunker] = None):
        """初始化LLM处理器
        
        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL
            model: 使用的模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间（秒）
            max_workers: 最大工作线程数
            enable_parallel: 是否启用并行处理
            chunk_size: 文档分块大小（token数）
            chunk_overlap: 文档分块重叠大小（token数）
            prompt_template: 自定义提示模板实例，如果为None则使用默认
            word_chunker: 自定义文档分块器实例，如果为None则使用默认
        """
        
        # 创建上下文日志器
        self.logger = create_logger_with_context({
            'component': 'LLMProcessor',
            'model': model,
            'max_workers': max_workers,
            'enable_parallel': enable_parallel
        })
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_workers = max_workers
        self.enable_parallel = enable_parallel
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.stream = stream
        self.force_json = force_json
        self.extra_body = extra_body
        
        # 初始化组件
        self.prompt_template = prompt_template if prompt_template is not None else PromptTemplate()
        self.word_chunker = word_chunker if word_chunker is not None else WordChunker(max_tokens=chunk_size, overlap_tokens=chunk_overlap)
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens_used': 0,
            'json_parsing_errors': 0
        }
    
    @log_execution_time()
    def process_chunk(self, 
                     chunk: str, 
                     doc_name: str = "未知文档") -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """处理文本块，生成知识图谱数据
        
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
            
            # 创建提示
            prompt = self._create_prompt(chunk, doc_name)
            process_logger.debug(f"📝 提示创建完成，长度: {len(prompt)} 字符")
            
            # 调用LLM API
            reasoning, response = self._call_llm_api(prompt)
            process_logger.debug(f"📡 API调用完成，响应长度: {len(response) if response else 0} 字符")
            
            # 提取JSON数据
            json_data = self._extract_json(response)

            # 为所有实体、状态和关系添加文档来源
            if json_data is not None:
                self._add_document_source_to_json_data(json_data, doc_name)

            processing_time = time.time() - start_time
            
            if json_data is None:
                self.stats['json_parsing_errors'] += 1
                self.stats['failed_requests'] += 1
                
                error_details = {
                    'success': False,
                    'error': 'JSON解析失败',
                    'error_type': 'json_parse_error',
                    'raw_response': response[:1000] if response else None,  # 增加到1000字符以便调试
                    'raw_response_length': len(response) if response else 0,
                    'processing_time': processing_time,
                    'chunk_length': len(chunk),
                    'reasoning_length': len(reasoning) if reasoning else 0
                }
                
                process_logger.error(f"❌ JSON解析失败")
                process_logger.debug(f"  📏 响应长度: {len(response) if response else 0}")
                process_logger.debug(f"  📄 响应预览: {response[:200] if response else 'None'}...")
                
                return None, error_details
            
            # 验证JSON数据质量
            validation_result = self._validate_extracted_data(json_data, process_logger)
            
            self.stats['successful_requests'] += 1
            
            success_details = {
                'success': True,
                'model': self.model,
                'chunk_length': len(chunk),
                'response_length': len(response) if response else 0,
                'processing_time': processing_time,
                'reasoning': reasoning,
                'reasoning_length': len(reasoning) if reasoning else 0,
                'validation': validation_result
            }
            
            process_logger.info(f"✅ 处理成功，耗时: {processing_time:.2f}s")
            
            return json_data, success_details
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats['failed_requests'] += 1
            error_msg = f"处理文本块失败: {str(e)}"
            
            process_logger.error(f"❌ {error_msg}")
            process_logger.debug(f"  ⏱️ 耗时: {processing_time:.2f}s")
            
            # 添加处理时间信息到异常中（如果需要的话，可以在调用者中捕获并使用）
            raise LLMProcessingError(error_msg) from e
    
    def _validate_extracted_data(self, json_data: Dict[str, Any], logger) -> Dict[str, Any]:
        """验证提取的JSON数据质量
        
        Args:
            json_data: 提取的JSON数据
            logger: 日志器
            
        Returns:
            验证结果信息
        """
        validation_result = {
            'structure_complete': True,
            'data_quality': 'good',
            'warnings': [],
            'statistics': {}
        }
        
        try:
            if not isinstance(json_data, dict):
                validation_result['warnings'].append('数据不是字典格式')
                validation_result['data_quality'] = 'poor'
                return validation_result
            
            # 检查必需字段
            expected_fields = ["基础实体", "状态实体", "状态关系"]
            missing_fields = []
            empty_fields = []
            
            for field in expected_fields:
                if field not in json_data:
                    missing_fields.append(field)
                    validation_result['structure_complete'] = False
                elif not json_data[field] or len(json_data[field]) == 0:
                    empty_fields.append(field)
            
            if missing_fields:
                validation_result['warnings'].append(f'缺少字段: {missing_fields}')
                validation_result['data_quality'] = 'poor'
                
            if empty_fields:
                validation_result['warnings'].append(f'空字段: {empty_fields}')
                if validation_result['data_quality'] == 'good':
                    validation_result['data_quality'] = 'fair'
            
            # 统计各字段的数据量
            for field in expected_fields:
                if field in json_data and isinstance(json_data[field], list):
                    count = len(json_data[field])
                    validation_result['statistics'][field] = count
                    logger.debug(f"📊 {field}: {count} 个条目")
            
            # 检查数据质量
            total_entities = sum(validation_result['statistics'].values())
            if total_entities == 0:
                validation_result['warnings'].append('没有提取到任何实体')
                validation_result['data_quality'] = 'poor'
            elif total_entities < 3:
                validation_result['warnings'].append('提取的实体数量较少')
                if validation_result['data_quality'] == 'good':
                    validation_result['data_quality'] = 'fair'
            
            logger.debug(f"✅ 数据验证完成: {validation_result['data_quality']} 质量，{total_entities} 个实体")
            
        except Exception as e:
            validation_result['warnings'].append(f'验证过程出错: {str(e)}')
            validation_result['data_quality'] = 'unknown'
            logger.warning(f"⚠️ 数据验证失败: {str(e)}")
        
        return validation_result
    
    def _create_prompt(self, chunk: str, doc_name: str) -> List[Dict[str, str]]:
        """创建提示（统一返回 messages 格式）
        
        Args:
            chunk: 文本块
            doc_name: 文档名称
            
        Returns:
            messages 列表
        """
        try:
            # 统一返回 messages 格式
            return self.prompt_template.create_prompt(
                chunk=chunk,
                doc_name=doc_name
            )
        except Exception as e:
            raise LLMProcessingError(f"创建提示失败: {str(e)}") from e
    
    def _call_llm_api(self, 
                     prompt: List[Dict[str, str]]) -> Tuple[str, str]:
        """调用LLM API
        
        Args:
            prompt: messages 列表
            
        Returns:
            LLM思考文本, LLM响应文本
            
        Raises:
            APIConnectionError: 当API调用失败时
        """
        # 创建API调用特定的上下文日志器
        api_logger = create_logger_with_context({
            'operation': 'api_call',
        })
        
        # prompt 已经是 messages 格式
        messages = prompt
        
        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": 0.7,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "stream": self.stream
        }
        
        # 如果强制JSON格式
        if self.force_json:
            request_params["response_format"] = {"type": "json_object"}
            
        if self.extra_body:
            request_params["extra_body"] = self.extra_body

        # 重试机制
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                api_logger.info(f"📡 开始API调用 (尝试 {attempt + 1}/{self.max_retries})")
                
                if self.stream or (self.extra_body and self.extra_body.get("enable_thinking", False)):
                    # thinking模式或stream模式, 使用流式响应
                    request_params["stream"] = True
                    return self._handle_stream_response(request_params)
                else:
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
                    api_logger.debug(f"  👀 响应预览: {response_content[:200] if response_content else 'None'}{'...' if response_content and len(response_content) > 200 else ''}")
                    
                    return '', response_content
                    
            except Exception as e:
                last_exception = e
                api_logger.warning(f"⚠️ API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                
                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (2 ** attempt)
                    api_logger.info(f"⏳ 等待 {sleep_time:.1f} 秒后重试...")
                    time.sleep(sleep_time)  # 指数退避
                    continue
                else:
                    break
        
        # 所有重试都失败了
        error_msg = f"API调用失败，已重试{self.max_retries}次: {str(last_exception)}"
        api_logger.error(f"❌ {error_msg}")
        raise APIConnectionError(error_msg) from last_exception
    
    def _handle_stream_response(self, request_params: Dict[str, Any]) -> Tuple[str, str]:
        """处理流式响应
        
        Args:
            request_params: 请求参数
            
        Returns:
            完整思考文本, 完整的响应文本
        """
        # 创建流式响应特定的上下文日志器
        stream_logger = create_logger_with_context({
            'operation': 'stream_response',
            'model': self.model
        })
        
        try:
            stream_logger.info("🌊 开始处理流式响应...")
            stream = self.client.chat.completions.create(**request_params)
            
            # 收集结果
            reasoning_parts: list[str] = []
            content_parts: list[str] = []
            usage_info = None
            chunk_count = 0
            last_content_chunk = 0  # 记录最后一个有内容的分块号
            
            for chunk in stream:
                chunk_count += 1
                
                # 检查chunk结构
                if not hasattr(chunk, 'choices') or not chunk.choices:
                    stream_logger.debug(f"📥 接收分块 #{chunk_count}: 无choices数据")
                    continue
                    
                delta = chunk.choices[0].delta
                if not delta:
                    stream_logger.debug(f"📥 接收分块 #{chunk_count}: 无delta数据")
                    continue

                # 记录详细的delta信息（仅在debug级别）
                stream_logger.debug(f"📥 接收分块 #{chunk_count}: {delta}")
                
                # 1. 思考内容（reasoning/reasoning_content）
                if hasattr(delta, "reasoning") and delta.reasoning:
                    reasoning_parts.append(delta.reasoning)
                    stream_logger.debug(f"🧠 分块 #{chunk_count}: 思考内容 {len(delta.reasoning)} 字符")
                elif hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    reasoning_parts.append(delta.reasoning_content)
                    stream_logger.debug(f"🧠 分块 #{chunk_count}: 思考内容 {len(delta.reasoning_content)} 字符")
                
                # 2. 正式回复（content）
                if delta.content:
                    content_parts.append(delta.content)
                    last_content_chunk = chunk_count
                    
                # 3. usage信息收集 - 更全面的处理
                if hasattr(chunk, "usage") and chunk.usage:
                    usage_info = chunk.usage
                    # stream_logger.debug(f"📊 分块 #{chunk_count}: 收到usage信息 {usage_info}")

            # 处理usage统计
            if usage_info:
                total_tokens = usage_info.total_tokens if hasattr(usage_info, 'total_tokens') else 0
                prompt_tokens = usage_info.prompt_tokens if hasattr(usage_info, 'prompt_tokens') else 0
                completion_tokens = usage_info.completion_tokens if hasattr(usage_info, 'completion_tokens') else 0
                
                self.stats['total_tokens_used'] += total_tokens
                
                stream_logger.info(f"📊 Token统计 - 输入: {prompt_tokens}, 输出: {completion_tokens}, 总计: {total_tokens}")
            else:
                stream_logger.warning("⚠️ 流式响应中未收到usage信息")

            full_reasoning = ''.join(reasoning_parts)
            full_content = ''.join(content_parts)

            # 记录流式响应统计
            stream_logger.info(f"✅ 流式响应处理完成!")
            stream_logger.info(f"  📊 接收分块数: {chunk_count}")
            stream_logger.info(f"  📝 最后内容分块: #{last_content_chunk}")
            stream_logger.info(f"  🧠 推理内容长度: {len(full_reasoning)} 字符")
            stream_logger.info(f"  💬 响应内容长度: {len(full_content)} 字符")
            
            # 检查内容是否被截断
            if chunk_count > 0 and last_content_chunk < chunk_count - 50:  # 如果最后50个分块都没有内容，可能被截断
                stream_logger.warning(f"⚠️ 可能的内容截断：最后内容分块 #{last_content_chunk}，总分块 #{chunk_count}")
            
            # 检查响应完整性
            if full_content:
                if not (full_content.rstrip().endswith('}') or full_content.rstrip().endswith(']')):
                    stream_logger.warning("⚠️ 响应内容可能不完整，未以}或]结尾")
            
            return full_reasoning, full_content

        except Exception as e:
            stream_logger.error(f"❌ 流式响应处理失败: {str(e)}")
            raise APIConnectionError(f"流式响应处理失败: {str(e)}") from e
    
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
        extract_logger.debug(f"📄 响应预览: {response[:500]}{'...' if len(response) > 500 else ''}")
        
        # 1. 首先尝试直接解析
        try:
            result = json.loads(response)
            extract_logger.info("✅ 直接JSON解析成功")
            return self._validate_json_structure(result, extract_logger)
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
            extract_logger.debug(f"📋 代码块模式匹配到 {len(matches)} 个结果")
            
            for i, match in enumerate(matches):
                try:
                    result = json.loads(match)
                    extract_logger.info(f"✅ JSON代码块解析成功 (第{i+1}个)")
                    return self._validate_json_structure(result, extract_logger)
                except json.JSONDecodeError as e:
                    extract_logger.debug(f"❌ 代码块 {i+1} 解析失败: {str(e)}")
                    continue
        
        # 3. 智能查找JSON对象 - 使用更精确的嵌套匹配
        extract_logger.debug("🔍 尝试智能JSON对象提取...")
        json_candidates = self._find_json_candidates(response, extract_logger)
        
        for i, candidate in enumerate(json_candidates):
            try:
                result = json.loads(candidate)
                extract_logger.info(f"✅ JSON对象解析成功 (候选项{i+1})")
                return self._validate_json_structure(result, extract_logger)
            except json.JSONDecodeError as e:
                extract_logger.debug(f"❌ 候选项 {i+1} 解析失败: {str(e)}")
                continue
        
        # 4. 使用json_repair尝试修复
        extract_logger.debug("🔧 尝试JSON修复...")
        repair_attempts = [
            response,  # 完整响应
            *json_candidates  # 所有候选项
        ]
        
        for i, content in enumerate(repair_attempts):
            if not content.strip():
                continue
                
            try:
                # 预处理：尝试修复常见的截断问题
                processed_content = self._preprocess_for_repair(content, extract_logger)
                repaired = json_repair.repair_json(processed_content)
                result = json.loads(repaired)
                extract_logger.info(f"✅ JSON修复成功 (尝试{i+1})")
                return self._validate_json_structure(result, extract_logger)
            except Exception as e:
                extract_logger.debug(f"❌ 修复尝试 {i+1} 失败: {str(e)}")
                continue
        
        extract_logger.error("❌ 所有JSON提取方法都失败了")
        return None
    
    def _find_json_candidates(self, text: str, logger) -> List[str]:
        """智能查找JSON候选项
        
        Args:
            text: 输入文本
            logger: 日志器
            
        Returns:
            JSON候选项列表，按质量排序
        """
        candidates = []
        
        # 方法1: 查找完整的大括号包围的内容
        brace_candidates = self._extract_balanced_braces(text)
        candidates.extend(brace_candidates)
        
        # 方法2: 查找从第一个 { 到最后一个 } 的内容
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            full_candidate = text[first_brace:last_brace + 1]
            if full_candidate not in candidates:
                candidates.append(full_candidate)
        
        # 方法3: 查找数组格式 [ ... ]
        first_bracket = text.find('[')
        last_bracket = text.rfind(']')
        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            array_candidate = text[first_bracket:last_bracket + 1]
            if array_candidate not in candidates:
                candidates.append(array_candidate)
        
        logger.debug(f"📋 找到 {len(candidates)} 个JSON候选项")
        
        # 按长度和完整性排序
        candidates.sort(key=lambda x: (len(x), x.count('{'), x.count('}')), reverse=True)
        
        return candidates[:10]  # 限制候选项数量，避免过多尝试
    
    def _extract_balanced_braces(self, text: str) -> List[str]:
        """提取平衡大括号的JSON内容
        
        Args:
            text: 输入文本
            
        Returns:
            平衡括号的内容列表
        """
        candidates = []
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
        
        return candidates
    
    def _preprocess_for_repair(self, content: str, logger) -> str:
        """预处理内容以提高JSON修复成功率
        
        Args:
            content: 原始内容
            logger: 日志器
            
        Returns:
            预处理后的内容
        """
        original_length = len(content)
        
        # 1. 移除可能的非JSON前缀和后缀
        content = content.strip()
        
        # 2. 检查是否以 { 开始，如果不是，尝试找到第一个 {
        if not content.startswith('{') and not content.startswith('['):
            first_brace = content.find('{')
            first_bracket = content.find('[')
            
            start_pos = -1
            if first_brace != -1 and first_bracket != -1:
                start_pos = min(first_brace, first_bracket)
            elif first_brace != -1:
                start_pos = first_brace
            elif first_bracket != -1:
                start_pos = first_bracket
            
            if start_pos != -1:
                content = content[start_pos:]
        
        # 3. 检查是否以 } 或 ] 结束，如果不是，可能被截断
        if not content.endswith('}') and not content.endswith(']'):
            logger.debug("⚠️ 检测到可能的JSON截断")
            
            # 尝试智能补全
            if content.startswith('{'):
                # 统计括号平衡
                open_braces = content.count('{')
                close_braces = content.count('}')
                missing_braces = open_braces - close_braces
                
                if missing_braces > 0:
                    # 检查最后是否有未完成的字符串
                    if content.rstrip().endswith('"') or content.rstrip().endswith(','):
                        content = content.rstrip().rstrip(',') + '}'
                    else:
                        content += '}' * missing_braces
                    logger.debug(f"🔧 补全了 {missing_braces} 个闭合括号")
            
            elif content.startswith('['):
                # 处理数组截断
                open_brackets = content.count('[')
                close_brackets = content.count(']')
                missing_brackets = open_brackets - close_brackets
                
                if missing_brackets > 0:
                    content += ']' * missing_brackets
                    logger.debug(f"🔧 补全了 {missing_brackets} 个闭合中括号")
        
        if len(content) != original_length:
            logger.debug(f"📝 预处理：长度从 {original_length} 变为 {len(content)}")
        
        return content
    
    def _validate_json_structure(self, json_data: Dict[str, Any], logger) -> Optional[Dict[str, Any]]:
        """验证JSON结构的完整性
        
        Args:
            json_data: 解析后的JSON数据
            logger: 日志器
            
        Returns:
            验证通过的JSON数据，失败返回None
        """
        if not isinstance(json_data, dict):
            logger.warning("⚠️ JSON数据不是字典格式")
            return json_data  # 仍然返回，可能是数组格式
        
        # 检查必需的顶级字段
        expected_fields = ["基础实体", "状态实体", "状态关系"]
        missing_fields = []
        
        for field in expected_fields:
            if field not in json_data:
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"⚠️ JSON结构不完整，缺少字段: {missing_fields}")
            # 不返回None，仍然接受部分数据，让上层决定如何处理
        
        # 检查数据质量
        total_entities = 0
        for field in expected_fields:
            if field in json_data and isinstance(json_data[field], list):
                count = len(json_data[field])
                total_entities += count
                logger.debug(f"📊 {field}: {count} 个条目")
        
        logger.info(f"✅ JSON结构验证完成，总计 {total_entities} 个实体")
        
        return json_data
    
    @log_execution_time()
    def batch_process(self, 
                     chunk_items: List[Tuple[str, int, str]], 
                     **kwargs) -> List[Tuple[Optional[Dict[str, Any]], Dict[str, Any]]]:
        """批量处理文本块
        
        Args:
            chunk_items: 包含(doc_name, chunk_index, chunk_content)的元组列表
            **kwargs: 传递给process_chunk的额外参数
            
        Returns:
            处理结果列表，保持与输入相同的顺序
        """
        if not self.enable_parallel or len(chunk_items) <= 1:
            # 串行处理
            return self._batch_process_serial(chunk_items, **kwargs)
        else:
            # 并行处理
            return self._batch_process_parallel(chunk_items, **kwargs)
    
    def _batch_process_serial(self, 
                             chunk_items: List[Tuple[str, int, str]], 
                             **kwargs) -> List[Tuple[Optional[Dict[str, Any]], Dict[str, Any]]]:
        """串行批量处理文本块
        
        Args:
            chunk_items: 包含(doc_name, chunk_index, chunk_content)的元组列表
            **kwargs: 传递给process_chunk的额外参数
            
        Returns:
            处理结果列表
        """
        results = []
        
        for i, (doc_name, chunk_index, chunk) in enumerate(chunk_items):
            start_time = time.time()
            try:
                process_logger = create_logger_with_context({
                    'operation': 'process_serial'
                })
                process_logger.debug(f"🔄 处理文档 '{doc_name}' 的分块 #{chunk_index}")
                result = self.process_chunk(chunk, doc_name, **kwargs)
                # 在结果中添加文档和分块信息
                # if result[1].get('success', False):
                result[1]['doc_name'] = doc_name
                result[1]['chunk_index'] = chunk_index
                result[1]['global_index'] = i
                results.append(result)
            except Exception as e:
                processing_time = time.time() - start_time
                error_info = {
                    'success': False,
                    'error': str(e),
                    'doc_name': doc_name,
                    'chunk_index': chunk_index,
                    'global_index': i,
                    'processing_time': processing_time
                }
                results.append((None, error_info))
        
        return results
    
    def _batch_process_parallel(self, 
                               chunk_items: List[Tuple[str, int, str]], 
                               **kwargs) -> List[Tuple[Optional[Dict[str, Any]], Dict[str, Any]]]:
        """并行批量处理文本块
        
        Args:
            chunk_items: 包含(doc_name, chunk_index, chunk_content)的元组列表
            **kwargs: 传递给process_chunk的额外参数
            
        Returns:
            处理结果列表
        """
        results = [None] * len(chunk_items)  # 预分配结果列表，保持顺序
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(self._process_chunk_with_metadata, i, doc_name, chunk_index, chunk, **kwargs): i 
                for i, (doc_name, chunk_index, chunk) in enumerate(chunk_items)
            }
            
            # 收集结果
            for future in as_completed(future_to_index):
                global_index = future_to_index[future]
                try:
                    results[global_index] = future.result()
                except Exception as e:
                    doc_name, chunk_index, _ = chunk_items[global_index]
                    error_info = {
                        'success': False,
                        'error': str(e),
                        'doc_name': doc_name,
                        'chunk_index': chunk_index,
                        'global_index': global_index,
                        'processing_time': None  # 在并行处理的异常情况下，无法准确计算处理时间
                    }
                    results[global_index] = (None, error_info)
        
        return results
    
    def _process_chunk_with_metadata(self, 
                                    global_index: int,
                                    doc_name: str,
                                    chunk_index: int,
                                    chunk: str, 
                                    **kwargs) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """带元数据的文本块处理（用于并行处理）
        
        Args:
            global_index: 全局索引
            doc_name: 文档名称
            chunk_index: 文档内分块索引
            chunk: 文本块内容
            **kwargs: 传递给process_chunk的额外参数
            
        Returns:
            处理结果
        """
        start_time = time.time()
        try:
            process_logger = create_logger_with_context({
                'operation': 'process_parallel'
            })
            process_logger.debug(f"🔄 处理文档 '{doc_name}' 的分块 #{chunk_index} (全局索引 #{global_index})")
            result = self.process_chunk(chunk, doc_name, **kwargs)
            # 在结果中添加文档和分块信息
            # if result[1].get('success', False):
            result[1]['doc_name'] = doc_name
            result[1]['chunk_index'] = chunk_index
            result[1]['global_index'] = global_index
            process_logger.debug(f"✅ 处理完成文档 '{doc_name}' 的分块 #{chunk_index} (全局索引 #{global_index})")
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            error_info = {
                'success': False,
                'error': str(e),
                'doc_name': doc_name,
                'chunk_index': chunk_index,
                'global_index': global_index,
                'processing_time': processing_time
            }
            process_logger.error(f"❌ 处理文档 '{doc_name}' 的分块 #{chunk_index} 失败: {str(e)}")
            return (None, error_info)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息
        
        Returns:
            统计信息字典
        """
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
    
    @log_execution_time()
    def process_documents(self, 
                         doc_paths: List[str],
                         include_tables: bool = True,
                         **kwargs) -> Dict[str, List[Tuple[Optional[Dict[str, Any]], Dict[str, Any]]]]:
        """批量处理文档列表
        
        Args:
            doc_paths: 文档路径列表
            include_tables: 是否包含表格处理
            **kwargs: 传递给process_chunk的额外参数
            
        Returns:
            以文档路径为键，处理结果列表为值的字典
        """
        # 收集所有文档的分块信息
        all_chunk_items = []
        doc_chunk_mapping = {}  # 记录每个文档的分块在全局列表中的位置
        
        for doc_path in doc_paths:
            try:
                # 获取文档名称
                doc_name = os.path.basename(doc_path)
                
                # 分块处理文档
                if doc_path.lower().endswith(('.docx', '.doc')):
                    # Word文档分块
                    chunks = self.word_chunker.chunk_document_with_tables(doc_path) if include_tables else self.word_chunker.chunk_document(doc_path)
                else:
                    # 纯文本文档分块
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    chunks = self._chunk_text(text)
                
                # 记录当前文档分块的起始位置
                start_index = len(all_chunk_items)
                
                # 将分块添加到全局列表
                for chunk_index, chunk in enumerate(chunks):
                    all_chunk_items.append((doc_name, chunk_index, chunk))
                
                # 记录文档分块映射
                doc_chunk_mapping[doc_path] = {
                    'start_index': start_index,
                    'chunk_count': len(chunks),
                    'doc_name': doc_name
                }
                
            except Exception as e:
                # 记录文档处理错误
                error_info = {
                    'success': False,
                    'error': f'文档分块失败: {str(e)}',
                    'doc_path': doc_path
                }
                doc_chunk_mapping[doc_path] = {
                    'start_index': len(all_chunk_items),
                    'chunk_count': 1,
                    'doc_name': os.path.basename(doc_path),
                    'error': error_info
                }
                # 添加错误占位符
                all_chunk_items.append((os.path.basename(doc_path), 0, ""))
        
        # 批量处理所有分块
        if all_chunk_items:
            all_results = self.batch_process(all_chunk_items, **kwargs)
        else:
            all_results = []
        
        # 将结果按文档重新组织
        results = {}
        for doc_path, mapping in doc_chunk_mapping.items():
            start_idx = mapping['start_index']
            chunk_count = mapping['chunk_count']
            
            if 'error' in mapping:
                # 文档分块失败的情况
                results[doc_path] = [(None, mapping['error'])]
            else:
                # 提取该文档的处理结果
                doc_results = all_results[start_idx:start_idx + chunk_count]
                results[doc_path] = doc_results
        
        return results
    
    @log_execution_time()
    def process_documents_streaming(self, 
                                   doc_paths: List[str],
                                   include_tables: bool = True,
                                   callback=None,
                                   **kwargs):
        """流式处理文档列表，避免内存积累
        
        Args:
            doc_paths: 文档路径列表
            include_tables: 是否包含表格处理
            callback: 回调函数，接收(doc_path, doc_results)参数
            **kwargs: 传递给process_chunk的额外参数
            
        Yields:
            (doc_path, doc_results) 元组
        """
        for doc_path in doc_paths:
            try:
                # 获取文档名称
                doc_name = os.path.basename(doc_path)
                
                # 分块处理文档
                if doc_path.lower().endswith(('.docx', '.doc')):
                    # Word文档分块
                    chunks = self.word_chunker.chunk_document_with_tables(doc_path) if include_tables else self.word_chunker.chunk_document(doc_path)
                else:
                    # 纯文本文档分块
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    chunks = self._chunk_text(text)
                
                # 准备分块项目
                chunk_items = [(doc_name, chunk_index, chunk) for chunk_index, chunk in enumerate(chunks)]
                
                # 处理当前文档的所有分块
                doc_results = self.batch_process(chunk_items, **kwargs)
                
                # 返回结果
                result = (doc_path, doc_results)
                
                # 如果有回调函数，调用它
                if callback:
                    callback(doc_path, doc_results)
                
                yield result
                
            except Exception as e:
                # 处理文档错误
                error_info = {
                    'success': False,
                    'error': f'文档处理失败: {str(e)}',
                    'doc_path': doc_path
                }
                error_result = (doc_path, [(None, error_info)])
                
                if callback:
                    callback(doc_path, [(None, error_info)])
                
                yield error_result
    
    @log_execution_time()
    def process_documents_streaming_optimized(self, 
                                            doc_paths: List[str],
                                            include_tables: bool = True,
                                            callback=None,
                                            batch_size: Optional[int] = None,
                                            **kwargs):
        """优化的流式处理文档列表，充分利用线程资源
        
        通过跨文档收集分块到缓冲池，确保每次批处理都能充分利用所有线程。
        当文档处理完成时立即返回结果，保持流式特性。
        
        Args:
            doc_paths: 文档路径列表
            include_tables: 是否包含表格处理
            callback: 回调函数，接收(doc_path, doc_results)参数
            batch_size: 批处理大小，默认为max_workers的2倍
            **kwargs: 传递给process_chunk的额外参数
            
        Yields:
            (doc_path, doc_results) 元组
        """
        from collections import deque
        
        # 确定批处理大小
        if batch_size is None:
            batch_size = max(self.max_workers * 2, 8)  # 默认为线程数的2倍，最少8个
        
        # 文档分块生成器
        def chunk_generator():
            for doc_path in doc_paths:
                try:
                    # 获取文档名称
                    doc_name = os.path.basename(doc_path)
                    
                    # 分块处理文档
                    if doc_path.lower().endswith(('.docx', '.doc')):
                        chunks = self.word_chunker.chunk_document_with_tables(doc_path) if include_tables else self.word_chunker.chunk_document(doc_path)
                    else:
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        chunks = self._chunk_text(text)
                    
                    # 生成分块项目
                    for chunk_index, chunk in enumerate(chunks):
                        yield {
                            'doc_path': doc_path,
                            'doc_name': doc_name,
                            'chunk_index': chunk_index,
                            'chunk': chunk,
                            'chunk_item': (doc_name, chunk_index, chunk)
                        }
                    
                    # 标记文档结束
                    yield {
                        'doc_path': doc_path,
                        'doc_name': doc_name,
                        'is_doc_end': True
                    }
                    
                except Exception as e:
                    # 文档处理错误
                    yield {
                        'doc_path': doc_path,
                        'doc_name': os.path.basename(doc_path),
                        'error': f'文档处理失败: {str(e)}',
                        'is_doc_end': True
                    }
        
        # 初始化状态
        chunk_buffer = []  # 分块缓冲池
        pending_docs = {}  # 待完成的文档 {doc_path: {'chunks': [], 'total_chunks': int}}
        chunk_gen = chunk_generator()
        
        try:
            while True:
                # 填充缓冲池直到达到批处理大小或没有更多分块
                while len(chunk_buffer) < batch_size:
                    try:
                        chunk_info = next(chunk_gen)
                        
                        if chunk_info.get('is_doc_end'):
                            # 文档结束标记
                            doc_path = chunk_info['doc_path']
                            
                            if chunk_info.get('error'):
                                # 文档处理错误
                                error_info = {
                                    'success': False,
                                    'error': chunk_info['error'],
                                    'doc_path': doc_path
                                }
                                error_result = (doc_path, [(None, error_info)])
                                
                                if callback:
                                    callback(doc_path, [(None, error_info)])
                                
                                yield error_result
                            else:
                                # 正常文档结束，标记总分块数
                                if doc_path in pending_docs:
                                    pending_docs[doc_path]['is_complete'] = True
                        else:
                            # 普通分块
                            doc_path = chunk_info['doc_path']
                            
                            # 添加到缓冲池
                            chunk_buffer.append(chunk_info)
                            
                            # 初始化或更新待完成文档信息
                            if doc_path not in pending_docs:
                                pending_docs[doc_path] = {
                                    'chunks': [],
                                    'chunk_results': {},
                                    'is_complete': False
                                }
                            
                    except StopIteration:
                        # 没有更多分块
                        break
                
                # 如果缓冲池为空，说明所有分块都处理完了
                if not chunk_buffer:
                    break
                
                # 批量处理缓冲池中的分块
                chunk_items = [info['chunk_item'] for info in chunk_buffer]
                batch_results = self.batch_process(chunk_items, **kwargs)
                
                # 将结果分配给对应的文档
                for i, chunk_info in enumerate(chunk_buffer):
                    doc_path = chunk_info['doc_path']
                    chunk_index = chunk_info['chunk_index']
                    result = batch_results[i]
                    
                    # 存储结果
                    pending_docs[doc_path]['chunk_results'][chunk_index] = result
                
                # 清空缓冲池
                chunk_buffer = []
                
                # 检查是否有文档可以完成并返回
                completed_docs = []
                for doc_path, doc_info in pending_docs.items():
                    if doc_info['is_complete']:
                        # 检查是否所有分块都已处理
                        chunk_results = doc_info['chunk_results']
                        if chunk_results:  # 确保有分块结果
                            # 按分块索引排序结果
                            sorted_results = [chunk_results[i] for i in sorted(chunk_results.keys())]
                            
                            result = (doc_path, sorted_results)
                            
                            if callback:
                                callback(doc_path, sorted_results)
                            
                            yield result
                            completed_docs.append(doc_path)
                
                # 移除已完成的文档
                for doc_path in completed_docs:
                    del pending_docs[doc_path]
                
        except Exception as e:
            # 处理意外错误
            for doc_path in pending_docs.keys():
                error_info = {
                    'success': False,
                    'error': f'批处理过程中发生错误: {str(e)}',
                    'doc_path': doc_path
                }
                error_result = (doc_path, [(None, error_info)])
                
                if callback:
                    callback(doc_path, [(None, error_info)])
                
                yield error_result
    
    def _chunk_text(self, text: str) -> List[str]:
        """将纯文本分块
        
        Args:
            text: 输入文本
            
        Returns:
            分块后的文本列表
        """
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        # 按段落分割
        paragraphs = text.split('\n')
        
        for para in paragraphs:
            if not para.strip():
                continue
                
            para_with_newline = para + '\n'
            para_tokens = self.word_chunker.estimate_tokens(para_with_newline)
            
            # 如果当前段落加上已有内容会超过最大token数，则结束当前分块
            if current_tokens + para_tokens > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # 保留重叠部分作为新分块的开始
                overlap_text = self.word_chunker._get_overlap_text(current_chunk)
                current_chunk = overlap_text + para_with_newline
                current_tokens = self.word_chunker.estimate_tokens(current_chunk)
            else:
                current_chunk += para_with_newline
                current_tokens += para_tokens
        
        # 添加最后一个分块
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def _add_document_source_to_json_data(self, json_data: Dict[str, Any], doc_name: str) -> None:
        """为JSON数据中的所有实体、状态和关系添加文档来源

        Args:
            json_data: LLM返回的JSON数据
            doc_name: 文档名称
        """
        if not isinstance(json_data, dict):
            return

        # 为基础实体添加文档来源
        if "基础实体" in json_data and isinstance(json_data["基础实体"], list):
            for entity in json_data["基础实体"]:
                if isinstance(entity, dict):
                    entity["文档来源"] = doc_name

        # 为状态实体添加文档来源
        if "状态实体" in json_data and isinstance(json_data["状态实体"], list):
            for state in json_data["状态实体"]:
                if isinstance(state, dict):
                    state["文档来源"] = doc_name

        # 为状态关系添加文档来源
        if "状态关系" in json_data and isinstance(json_data["状态关系"], list):
            for relation in json_data["状态关系"]:
                if isinstance(relation, dict):
                    relation["文档来源"] = doc_name