#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM JSON Generator 运行模式

提供不同的文档处理运行模式，包括批量处理和优化流式处理。
从complete_document_processing_example.py中提取的模式1和模式3。
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .processor import LLMProcessor
from .config import ConfigManager
from .utils import (
    ensure_dir,
    save_json,
    load_json,
    Timer,
    sanitize_filename,
    merge_knowledge_graph_results
)
from .log import (
    setup_logging,
    get_logger,
    create_logger_with_context,
    create_timed_logger,
    log_execution_time,
    log_system_info
)
from .exceptions import LLMProcessingError, ValidationError
from .word_chunker import WordChunker
from .validator import DataValidator
from .utils import chunk_text
from .prompt_template import PromptTemplate

class DocumentProcessor:
    """文档处理器 - 提供多种处理模式"""
    
    def __init__(self, config_path: str = "config.json", template_file: Optional[str] = None):
        """初始化处理器
        
        Args:
            config_path: 配置文件路径
        """
        # 初始化日志系统
        
        self.config_path = config_path
        self.config = ConfigManager(config_path)
        
        # 创建上下文日志器
        self.logger = create_logger_with_context({
            'component': 'DocumentProcessor',
            'config_path': config_path,
            'template_file': template_file
        })
        
        # 初始化LLM处理器
        merged_config = self.config.get_merged_config()
        
        if template_file:
            self.prompt_template = PromptTemplate(template_file)
            self.llm_processor = LLMProcessor(**merged_config, prompt_template=self.prompt_template)
        else:
            self.llm_processor = LLMProcessor(**merged_config)
        
        # 初始化Word分块器
        self.word_chunker = WordChunker(
            max_tokens=self.config.processing_config.chunk_size,
            overlap_tokens=self.config.processing_config.chunk_overlap
        )
        
        # 初始化验证器
        self.validator = DataValidator()
    
    @log_execution_time()
    def _scan_folder_for_documents(self, folder_path: str) -> List[str]:
        """扫描文件夹获取支持的文档文件
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            文档文件路径列表
        """
        supported_extensions = {'.txt', '.docx', '.doc'}
        doc_files = []
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = Path(file_path).suffix.lower()
                    
                    if file_ext in supported_extensions:
                        doc_files.append(file_path)
                        self.logger.debug(f"📄 找到文档文件: {file_path}")
            
            # 按文件名排序
            doc_files.sort()
            self.logger.info(f"📊 在文件夹 {folder_path} 中找到 {len(doc_files)} 个支持的文档文件")
            
        except Exception as e:
            self.logger.error(f"❌ 扫描文件夹时发生错误: {e}")
            return []
        
        return doc_files
    
    @log_execution_time()
    def process_document_list_batch(self, 
                                   folder_path: str,
                                   base_output_dir: str = "output",
                                   include_tables: bool = True,
                                   generate_validation_report: bool = True) -> Dict[str, Any]:
        """传统批量处理 (一次性加载所有文档)
        
        Args:
            folder_path: 文档文件夹路径
            base_output_dir: 基础输出目录
            include_tables: 是否包含表格处理
            generate_validation_report: 是否生成验证报告
            
        Returns:
            处理结果字典
        """
        # 创建带上下文的日志器
        batch_logger = create_logger_with_context({
            'mode': 'batch_processing',
            'folder_path': folder_path,
            'output_dir': base_output_dir,
            'include_tables': include_tables,
            'validation': generate_validation_report
        })
        
        start_time = time.time()
        
        # 检查文件夹是否存在
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            batch_logger.error(f"📁 文件夹不存在或不是有效目录: {folder_path}")
            return {
                'success': False,
                'error': f'文件夹不存在或不是有效目录: {folder_path}',
                'processing_time': 0
            }
        
        # 扫描文件夹获取文档文件
        doc_paths = self._scan_folder_for_documents(folder_path)
        
        if not doc_paths:
            batch_logger.warning(f"📁 文件夹中未找到支持的文档文件: {folder_path}")
            return {
                'success': False,
                'error': '文件夹中未找到支持的文档文件',
                'processing_time': 0
            }
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(base_output_dir, f"batch_processing_{timestamp}")
        ensure_dir(output_dir)
        
        batch_logger.info(f"📁 扫描文件夹: {folder_path}")
        batch_logger.info(f"📊 找到 {len(doc_paths)} 个文档文件")
        batch_logger.info(f"📂 输出目录: {output_dir}")
        
        document_results = {}
        
        # 使用LLMProcessor的批量处理方法
        try:
            batch_logger.info("🚀 开始批量处理所有文档...")
            
            # 使用processor的process_documents方法
            batch_results = self.llm_processor.process_documents(
                doc_paths, include_tables=include_tables
            )
            
            # 处理每个文档的结果
            for doc_path, doc_chunk_results in batch_results.items():
                try:
                    doc_start_time = time.time()
                    batch_logger.info(f"📄 处理文档结果: {doc_path}")
                    
                    # 转换结果格式，保留完整的processing_info
                    chunk_results = []
                    for i, (result, info) in enumerate(doc_chunk_results):
                        chunk_results.append({
                            'chunk_index': i,
                            'result': result if info['success'] else None,
                            'success': info['success'],
                            'error': info.get('error') if not info['success'] else None,
                            'processing_time': info.get('processing_time', 0),
                            # 保留完整的processing_info
                            'full_info': info
                        })
                    
                    # 处理单个文档的结果
                    doc_result = self._process_document_results(
                        doc_path, chunk_results, output_dir, generate_validation_report
                    )
                    
                    doc_result['processing_time'] = time.time() - doc_start_time
                    document_results[doc_path] = doc_result
                    
                    if doc_result['success']:
                        batch_logger.info(f"✅ 文档处理成功: {doc_path}")
                    else:
                        batch_logger.error(f"❌ 文档处理失败: {doc_path} - {doc_result.get('error')}")
                        
                except Exception as e:
                    batch_logger.error(f"❌ 处理文档结果时发生错误: {doc_path} - {e}")
                    document_results[doc_path] = {
                        'success': False,
                        'error': f"结果处理失败: {e}",
                        'processing_time': 0
                    }
        
        except Exception as e:
            batch_logger.error(f"❌ 批量处理过程中发生错误: {e}")
            # 为所有文档添加错误记录
            for doc_path in doc_paths:
                if doc_path not in document_results:
                    document_results[doc_path] = {
                        'success': False,
                        'error': f"批量处理失败: {e}",
                        'processing_time': 0
                    }
        
        total_time = time.time() - start_time
        
        # 生成最终结果
        results = self._generate_final_results(
            document_results, output_dir, total_time, "batch_processing"
        )
        
        # 显示结果
        self._display_results(results)
        
        return results
    
    @log_execution_time()
    def process_document_list_streaming_optimized(self,
                                                 folder_path: str,
                                                 base_output_dir: str = "output",
                                                 include_tables: bool = True,
                                                 generate_validation_report: bool = True) -> Dict[str, Any]:
        """优化流式处理 (批量流式处理，充分利用线程资源)
        
        Args:
            folder_path: 文档文件夹路径
            base_output_dir: 基础输出目录
            include_tables: 是否包含表格处理
            generate_validation_report: 是否生成验证报告
            
        Returns:
            处理结果字典
        """
        # 创建带上下文的日志器
        streaming_logger = create_logger_with_context({
            'mode': 'streaming_optimized',
            'folder_path': folder_path,
            'output_dir': base_output_dir,
            'include_tables': include_tables,
            'validation': generate_validation_report
        })
        
        start_time = time.time()
        
        # 检查文件夹是否存在
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            streaming_logger.error(f"📁 文件夹不存在或不是有效目录: {folder_path}")
            return {
                'success': False,
                'error': f'文件夹不存在或不是有效目录: {folder_path}',
                'processing_time': 0
            }
        
        # 扫描文件夹获取文档文件
        doc_paths = self._scan_folder_for_documents(folder_path)
        
        if not doc_paths:
            streaming_logger.warning(f"📁 文件夹中未找到支持的文档文件: {folder_path}")
            return {
                'success': False,
                'error': '文件夹中未找到支持的文档文件',
                'processing_time': 0
            }
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(base_output_dir, f"streaming_optimized_{timestamp}")
        ensure_dir(output_dir)
        
        streaming_logger.info(f"📁 扫描文件夹: {folder_path}")
        streaming_logger.info(f"📊 找到 {len(doc_paths)} 个文档文件")
        streaming_logger.info(f"📂 输出目录: {output_dir}")
        
        document_results = {}
        
        # 使用LLMProcessor的优化流式处理方法
        try:
            streaming_logger.info("🚀 开始优化流式处理所有文档...")
            
            # 使用processor的process_documents_streaming_optimized方法
            for doc_path, doc_chunk_results in self.llm_processor.process_documents_streaming_optimized(
                doc_paths, include_tables=include_tables
            ):
                try:
                    # 转换结果格式，保留完整的processing_info
                    chunk_results = []
                    for i, (result, info) in enumerate(doc_chunk_results):
                        chunk_results.append({
                            'chunk_index': i,
                            'result': result if info['success'] else None,
                            'success': info['success'],
                            'error': info.get('error') if not info['success'] else None,
                            'processing_time': info.get('processing_time', 0),
                            # 保留完整的processing_info
                            'full_info': info
                        })
                    
                    # 处理单个文档的结果
                    doc_result = self._process_document_results(
                        doc_path, chunk_results, output_dir, generate_validation_report
                    )
                    
                    document_results[doc_path] = doc_result
                    
                    # 进度显示
                    status = "✅" if doc_result['success'] else "❌"
                    streaming_logger.info(f"{status} 文档处理完成: {Path(doc_path).name}")
                    
                except Exception as e:
                    streaming_logger.error(f"❌ 处理文档结果时发生错误: {doc_path} - {e}")
                    document_results[doc_path] = {
                        'success': False,
                        'error': f"结果处理失败: {e}",
                        'processing_time': 0
                    }
        
        except Exception as e:
            streaming_logger.error(f"❌ 优化流式处理过程中发生错误: {e}")
            # 为所有未处理的文档添加错误记录
            for doc_path in doc_paths:
                if doc_path not in document_results:
                    document_results[doc_path] = {
                        'success': False,
                        'error': f"流式处理失败: {e}",
                        'processing_time': 0
                    }
        
        total_time = time.time() - start_time
        
        # 生成最终结果
        results = self._generate_final_results(
            document_results, output_dir, total_time, "streaming_optimized"
        )
        
        # 显示结果
        self._display_results(results)
        
        return results
    
    def _get_document_chunks(self, doc_path: str, include_tables: bool = True) -> List[str]:
        """获取文档分块"""
        file_ext = Path(doc_path).suffix.lower()
        
        if file_ext in ['.docx', '.doc']:
            # Word文档处理
            if include_tables:
                return self.word_chunker.chunk_document_with_tables(doc_path)
            else:
                return self.word_chunker.chunk_document(doc_path)
        else:
            # 纯文本文件处理
            with open(doc_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            from .utils import chunk_text
            return chunk_text(
                text,
                self.config.processing_config.chunk_size,
                self.config.processing_config.chunk_overlap
            )
    
    def _process_document_results(self, 
                                doc_path: str, 
                                chunk_results: List[Dict[str, Any]], 
                                output_dir: str,
                                generate_validation_report: bool = True) -> Dict[str, Any]:
        """处理文档结果"""
        doc_name = Path(doc_path).stem
        safe_doc_name = sanitize_filename(doc_name)
        
        # 创建文档输出目录
        doc_output_dir = os.path.join(output_dir, safe_doc_name)
        ensure_dir(doc_output_dir)
        
        # 分离成功和失败的结果，保留详细信息
        successful_results = []
        failed_chunks = []
        detailed_chunk_info = []
        processing_stats = {
            'total_processing_time': 0,
            'total_chunk_length': 0,
            'total_response_length': 0,
            'reasoning_available_count': 0,
            'model_used': None
        }
        
        for chunk_result in chunk_results:
            chunk_index = chunk_result['chunk_index']
            full_info = chunk_result.get('full_info', {})
            
            # 构建详细的分块信息
            chunk_detail = {
                'chunk_index': chunk_index,
                'success': chunk_result['success'],
                'processing_time': chunk_result.get('processing_time', 0),
                'error': chunk_result.get('error') if not chunk_result['success'] else None,
                # 从full_info中提取详细信息
                'model': full_info.get('model'),
                'chunk_length': full_info.get('chunk_length', 0),
                'response_length': full_info.get('response_length', 0),
                'has_reasoning': bool(full_info.get('reasoning', '')),
                'reasoning_length': len(full_info.get('reasoning', '')),
                'doc_name': full_info.get('doc_name'),
                'global_index': full_info.get('global_index'),
                'raw_response_preview': full_info.get('raw_response', '')[:200] if not chunk_result['success'] else None
            }
            
            # 更新统计信息
            processing_stats['total_processing_time'] += chunk_result.get('processing_time', 0)
            processing_stats['total_chunk_length'] += full_info.get('chunk_length', 0)
            processing_stats['total_response_length'] += full_info.get('response_length', 0)
            
            if full_info.get('reasoning'):
                processing_stats['reasoning_available_count'] += 1
            
            if not processing_stats['model_used'] and full_info.get('model'):
                processing_stats['model_used'] = full_info.get('model')
            
            if chunk_result['success'] and chunk_result['result']:
                successful_results.append(chunk_result['result'])
                
                chunk_detail.update({
                    'entity_counts': {
                        'basic_entities': len(chunk_result['result'].get('基础实体', [])),
                        'state_entities': len(chunk_result['result'].get('状态实体', [])),
                        'relations': len(chunk_result['result'].get('状态关系', []))
                    }
                })
            else:
                failed_chunks.append({
                    'chunk_index': chunk_index,
                    'error': chunk_result.get('error', '未知错误'),
                    'processing_time': chunk_result.get('processing_time', 0),
                    'model': full_info.get('model'),
                    'chunk_length': full_info.get('chunk_length', 0),
                    'raw_response_preview': full_info.get('raw_response', '')[:500] if full_info.get('raw_response') else None
                })
            
            detailed_chunk_info.append(chunk_detail)
        
        # 保存详细的分块结果
        chunks_file = os.path.join(doc_output_dir, "chunks_results.json")
        save_json({
            'document_info': {
                'document_path': doc_path,
                'document_name': doc_name,
                'processing_timestamp': datetime.now().isoformat()
            },
            'processing_summary': {
                'total_chunks': len(chunk_results),
                'successful_chunks': len(successful_results),
                'failed_chunks': len(failed_chunks),
                'success_rate': (len(successful_results) / len(chunk_results) * 100) if chunk_results else 0,
                'total_processing_time': processing_stats['total_processing_time'],
                'average_processing_time': processing_stats['total_processing_time'] / len(chunk_results) if chunk_results else 0,
                'total_chunk_length': processing_stats['total_chunk_length'],
                'total_response_length': processing_stats['total_response_length'],
                'average_chunk_length': processing_stats['total_chunk_length'] / len(chunk_results) if chunk_results else 0,
                'average_response_length': processing_stats['total_response_length'] / len(successful_results) if successful_results else 0,
                'reasoning_available_count': processing_stats['reasoning_available_count'],
                'reasoning_coverage': (processing_stats['reasoning_available_count'] / len(chunk_results) * 100) if chunk_results else 0,
                'model_used': processing_stats['model_used']
            },
            'detailed_chunks': detailed_chunk_info,
            'successful_chunks_data': successful_results,
            'failed_chunks': failed_chunks
        }, chunks_file)
        
        # 如果有reasoning数据，单独保存
        reasoning_data = []
        for chunk_result in chunk_results:
            full_info = chunk_result.get('full_info', {})
            reasoning = full_info.get('reasoning', '')
            if reasoning:
                reasoning_data.append({
                    'chunk_index': chunk_result['chunk_index'],
                    'reasoning': reasoning,
                    'success': chunk_result['success']
                })
        
        if reasoning_data:
            reasoning_file = os.path.join(doc_output_dir, "reasoning_data.json")
            save_json({
                'document_name': doc_name,
                'reasoning_chunks': reasoning_data,
                'summary': {
                    'total_reasoning_chunks': len(reasoning_data),
                    'coverage': (len(reasoning_data) / len(chunk_results) * 100) if chunk_results else 0
                }
            }, reasoning_file)
        
        if not successful_results:
            # 计算处理时间（从chunk_results中获取）
            processing_time = sum(chunk.get('processing_time', 0) for chunk in chunk_results)
            
            return {
                'success': False,
                'error': '所有分块处理都失败了',
                'output_directory': doc_output_dir,
                'processing_time': processing_time,
                'chunks': {
                    'total': len(chunk_results),
                    'successful': 0,
                    'failed': len(failed_chunks),
                    'success_rate': 0
                }
            }
        
        # 合并结果
        merged_data = merge_knowledge_graph_results(successful_results)
        
        # 如果有失败的块，保存失败信息
        failed_file = None
        if failed_chunks:
            failed_file = os.path.join(doc_output_dir, "failed_chunks.json")
            save_json({
                'document_info': {
                    'document_path': doc_path,
                    'document_name': doc_name,
                    'processing_timestamp': datetime.now().isoformat()
                },
                'failed_summary': {
                    'total_failed_chunks': len(failed_chunks),
                    'total_chunks': len(chunk_results)
                },
                'failed_chunks': failed_chunks
            }, failed_file)
            self.logger.warning(f"失败信息已保存: {failed_file}")
        
        # 保存合并结果
        merged_file = os.path.join(doc_output_dir, "merged_data.json")
        save_json(merged_data, merged_file)
        
        # 数据验证
        validation_result = None
        if generate_validation_report:
            try:
                validated_data, validation_report = self.validator.validate_data(merged_data)
                validation_result = self.validator.get_validation_summary()
                
                # 保存验证报告
                self.validator.export_validation_report(
                    os.path.join(doc_output_dir, "validation_report.json")
                )
                
                # 保存验证后的数据
                save_json(validated_data, os.path.join(doc_output_dir, "validated_data.json"))
                
            except Exception as e:
                self.logger.warning(f"⚠️ 数据验证失败: {e}")
        
        # 获取LLM统计信息
        llm_stats = self.llm_processor.get_stats()
        
        # 计算处理时间（从chunk_results中获取）
        processing_time = sum(chunk.get('processing_time', 0) for chunk in chunk_results)
        
        return {
            'success': True,
            'output_directory': doc_output_dir,
            'processing_time': processing_time,
            'chunks': {
                'total': len(chunk_results),
                'successful': len(successful_results),
                'failed': len(failed_chunks),
                'success_rate': (len(successful_results) / len(chunk_results) * 100) if chunk_results else 0
            },
            'entities': {
                'total': len(merged_data['基础实体']) + len(merged_data['状态实体']),
                'basic_entities': len(merged_data['基础实体']),
                'state_entities': len(merged_data['状态实体'])
            },
            'relations': {
                'total': len(merged_data['状态关系'])
            },
            'processing_stats': {
                'total_processing_time': processing_stats['total_processing_time'],
                'average_processing_time': processing_stats['total_processing_time'] / len(chunk_results) if chunk_results else 0,
                'total_chunk_length': processing_stats['total_chunk_length'],
                'total_response_length': processing_stats['total_response_length'],
                'average_chunk_length': processing_stats['total_chunk_length'] / len(chunk_results) if chunk_results else 0,
                'average_response_length': processing_stats['total_response_length'] / len(successful_results) if successful_results else 0,
                'reasoning_available_count': processing_stats['reasoning_available_count'],
                'reasoning_coverage': (processing_stats['reasoning_available_count'] / len(chunk_results) * 100) if chunk_results else 0,
                'model_used': processing_stats['model_used']
            },
            'files': {
                'chunks_results': chunks_file,
                'merged_data': merged_file,
                'failed_file': failed_file,
                'reasoning_data': os.path.join(doc_output_dir, "reasoning_data.json") if reasoning_data else None,
                'validation_report': os.path.join(doc_output_dir, "validation_report.json") if validation_result else None,
                'validated_data': os.path.join(doc_output_dir, "validated_data.json") if validation_result else None
            },
            'llm_stats': llm_stats,
            'validation': validation_result
        }
    
    def _generate_final_results(self, 
                              document_results: Dict[str, Any], 
                              output_dir: str, 
                              total_time: float,
                              processing_mode: str) -> Dict[str, Any]:
        """生成最终结果"""
        # 生成处理摘要
        summary = self._generate_summary(document_results, total_time)
        
        # 保存最终报告
        final_report = {
            'processing_info': {
                'mode': processing_mode,
                'model': self.config.llm_config.model,
                'timestamp': datetime.now().isoformat(),
                'output_directory': output_dir,
                'config': {
                    'chunk_size': self.config.processing_config.chunk_size,
                    'chunk_overlap': self.config.processing_config.chunk_overlap,
                    'parallel_processing': self.config.processing_config.enable_parallel,
                    'max_workers': self.config.processing_config.max_workers
                }
            },
            'summary': summary,
            'document_results': document_results
        }
        
        # 保存最终报告
        report_file = os.path.join(output_dir, "final_report.json")
        save_json(final_report, report_file)
        
        # 合并所有文档的merged_data.json
        merged_kg_file = os.path.join(output_dir, "all_documents_merged_knowledge_graph.json")
        self.merge_all_documents_knowledge_graph(
            [res['files']['merged_data'] for res in document_results.values() if res.get('files', {}).get('merged_data')],
            merged_kg_file
        )
        
        # 判断是否有验证后的数据需要合并
        validated_files = [res['files']['validation_report'] for res in document_results.values() if res.get('files', {}).get('validation_report')]
        if validated_files:
            merged_validated_file = os.path.join(output_dir, "all_documents_validated_data.json")
            self.merge_all_documents_knowledge_graph(
                [res['files']['validated_data'] for res in document_results.values() if res.get('files', {}).get('validated_data')],
                merged_validated_file
            )

        return final_report
    
    def merge_all_documents_knowledge_graph(self, file_paths: List[str], output_path: str) -> Dict[str, Any]:
        """合并所有文档的知识图谱结果"""
        all_merged_entities = {
            '基础实体': [],
            '状态实体': [],
            '状态关系': []
        }
        for file_path in file_paths:
            if os.path.exists(file_path):
                merged_data = load_json(file_path)
                all_merged_entities['基础实体'].extend(merged_data.get('基础实体', []))
                all_merged_entities['状态实体'].extend(merged_data.get('状态实体', []))
                all_merged_entities['状态关系'].extend(merged_data.get('状态关系', []))
        save_json(all_merged_entities, output_path)
        return all_merged_entities

    def _generate_summary(self, document_results: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """生成处理摘要"""
        successful_docs = sum(1 for result in document_results.values() if result.get('success', False))
        total_docs = len(document_results)
        
        total_chunks = 0
        total_successful_chunks = 0
        total_entities = 0
        total_relations = 0
        
        for result in document_results.values():
            if result.get('success'):
                chunks_info = result.get('chunks', {})
                total_chunks += chunks_info.get('total', 0)
                total_successful_chunks += chunks_info.get('successful', 0)
                
                entities_info = result.get('entities', {})
                total_entities += entities_info.get('total', 0)
                
                relations_info = result.get('relations', {})
                total_relations += relations_info.get('total', 0)
        
        return {
            'documents': {
                'total': total_docs,
                'successful': successful_docs,
                'failed': total_docs - successful_docs,
                'success_rate': (successful_docs / total_docs * 100) if total_docs > 0 else 0
            },
            'chunks': {
                'total': total_chunks,
                'successful': total_successful_chunks,
                'failed': total_chunks - total_successful_chunks,
                'success_rate': (total_successful_chunks / total_chunks * 100) if total_chunks > 0 else 0
            },
            'knowledge_graph': {
                'total_entities': total_entities,
                'total_relations': total_relations
            },
            'performance': {
                'total_processing_time': total_time,
                'avg_time_per_document': total_time / total_docs if total_docs > 0 else 0
            }
        }
    
    def _display_results(self, results: Dict[str, Any]):
        """显示处理结果"""
        print("\n" + "=" * 60)
        print("文档处理完成！")
        print("=" * 60)
        
        # 基本信息
        info = results['processing_info']
        print(f"\n📊 处理信息:")
        print(f"  模式: {info['mode']}")
        print(f"  模型: {info['model']}")
        print(f"  处理时间: {info['timestamp']}")
        print(f"  输出目录: {info['output_directory']}")
        
        # 配置信息
        config = info['config']
        print(f"\n⚙️ 配置参数:")
        print(f"  分块大小: {config['chunk_size']} tokens")
        print(f"  重叠大小: {config['chunk_overlap']} tokens")
        print(f"  并行处理: {config['parallel_processing']}")
        print(f"  最大线程数: {config['max_workers']}")
        
        # 处理摘要
        summary = results['summary']
        print(f"\n📈 处理摘要:")
        print(f"  文档总数: {summary['documents']['total']}")
        print(f"  成功文档: {summary['documents']['successful']}")
        print(f"  文档成功率: {summary['documents']['success_rate']:.1f}%")
        print(f"  分块总数: {summary['chunks']['total']}")
        print(f"  成功分块: {summary['chunks']['successful']}")
        print(f"  分块成功率: {summary['chunks']['success_rate']:.1f}%")
        print(f"  总实体数: {summary['knowledge_graph']['total_entities']}")
        print(f"  总关系数: {summary['knowledge_graph']['total_relations']}")
        print(f"  总处理时间: {summary['performance']['total_processing_time']:.2f}秒")
        
        # 各文档详情
        print(f"\n📄 各文档处理详情:")
        for doc_path, result in results['document_results'].items():
            doc_name = os.path.basename(doc_path)
            if result.get('success'):
                chunks = result['chunks']
                entities = result['entities']
                relations = result['relations']
                proc_stats = result.get('processing_stats', {})
                
                print(f"  ✅ {doc_name}:")
                print(f"     分块: {chunks['successful']}/{chunks['total']} ({chunks['success_rate']:.1f}%)")
                print(f"     实体: {entities['total']} (基础: {entities['basic_entities']}, 状态: {entities['state_entities']})")
                print(f"     关系: {relations['total']}")
                print(f"     时间: {result['processing_time']:.2f}秒")
                
                # 显示新增的详细统计信息
                if proc_stats:
                    print(f"     平均分块长度: {proc_stats.get('average_chunk_length', 0):.0f} 字符")
                    print(f"     平均响应长度: {proc_stats.get('average_response_length', 0):.0f} 字符")
                    if proc_stats.get('reasoning_available_count', 0) > 0:
                        print(f"     推理覆盖率: {proc_stats.get('reasoning_coverage', 0):.1f}% ({proc_stats.get('reasoning_available_count', 0)} 个分块)")
                    print(f"     使用模型: {proc_stats.get('model_used', 'Unknown')}")
                
                print(f"     输出: {result['output_directory']}")
            else:
                print(f"  ❌ {doc_name}: {result.get('error', '处理失败')}")
        
        print(f"\n✨ 处理完成！查看输出目录获取详细结果。")
    
    @log_execution_time()
    def process_single_document(self,
                                document_path: str,
                                base_output_dir: str = "output",
                                include_tables: bool = True,
                                generate_validation_report: bool = True) -> Dict[str, Any]:
        """处理单个文档

        Args:
            document_path: 文档文件夹路径
            base_output_dir: 基础输出目录
            include_tables: 是否包含表格处理
            generate_validation_report: 是否生成验证报告
            
        Returns:
            处理结果字典
        """
        # 创建带上下文的日志器
        single_logger = create_logger_with_context({
            'mode': 'single_document',
            'document_path': document_path,
            'output_dir': base_output_dir,
            'include_tables': include_tables,
            'validation': generate_validation_report
        })
        
        start_time = time.time()
        
        # 检查输入文件
        if not os.path.exists(document_path):
            single_logger.error(f"📄 输入文件不存在: {document_path}")
            return {
                'success': False,
                'error': f'输入文件不存在: {document_path}',
                'processing_time': 0
            }

        doc_paths = [document_path]

        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(base_output_dir, f"streaming_optimized_{timestamp}")
        ensure_dir(output_dir)
        
        single_logger.info(f"📂 输出目录: {output_dir}")
        
        document_results = {}
        
        # 使用LLMProcessor的优化流式处理方法
        try:
            single_logger.info("🚀 开始处理文档...")
            
            # 使用processor的process_documents_streaming_optimized方法
            for doc_path, doc_chunk_results in self.llm_processor.process_documents_streaming_optimized(
                doc_paths, include_tables=include_tables
            ):
                try:
                    # 转换结果格式，保留完整的processing_info
                    chunk_results = []
                    for i, (result, info) in enumerate(doc_chunk_results):
                        chunk_results.append({
                            'chunk_index': i,
                            'result': result if info['success'] else None,
                            'success': info['success'],
                            'error': info.get('error') if not info['success'] else None,
                            'processing_time': info.get('processing_time', 0),
                            # 保留完整的processing_info
                            'full_info': info
                        })
                    
                    # 处理单个文档的结果
                    doc_result = self._process_document_results(
                        doc_path, chunk_results, output_dir, generate_validation_report
                    )
                    
                    document_results[doc_path] = doc_result
                    
                    # 进度显示
                    status = "✅" if doc_result['success'] else "❌"
                    single_logger.info(f"{status} 文档处理完成: {Path(doc_path).name}")
                    
                except Exception as e:
                    single_logger.error(f"❌ 处理文档结果时发生错误: {doc_path} - {e}")
                    document_results[doc_path] = {
                        'success': False,
                        'error': f"结果处理失败: {e}",
                        'processing_time': 0
                    }
        
        except Exception as e:
            single_logger.error(f"❌ 优化流式处理过程中发生错误: {e}")
            # 为所有未处理的文档添加错误记录
            for doc_path in doc_paths:
                if doc_path not in document_results:
                    document_results[doc_path] = {
                        'success': False,
                        'error': f"流式处理失败: {e}",
                        'processing_time': 0
                    }
        
        total_time = time.time() - start_time
        
        # 生成最终结果
        result = document_results[document_path]
        
        return result
        
    # def process_single_document(self,
    #                            input_path: str,
    #                            output_dir: str = "output",
    #                            doc_name: Optional[str] = None,
    #                            chunk_size: Optional[int] = None,
    #                            chunk_overlap: Optional[int] = None,
    #                            include_tables: bool = True,
    #                            verbose: bool = False) -> Dict[str, Any]:
    #     """处理单个文档（逐个处理文本块）
        
    #     Args:
    #         input_path: 输入文件路径
    #         output_dir: 输出目录
    #         doc_name: 文档名称（默认使用文件名）
    #         chunk_size: 文本块大小（覆盖配置）
    #         chunk_overlap: 文本块重叠大小（覆盖配置）
    #         include_tables: 是否包含表格处理
    #         verbose: 详细输出
            
    #     Returns:
    #         处理结果字典
    #     """
    #     start_time = time.time()
        
    #     # 检查输入文件
    #     if not os.path.exists(input_path):
    #         return {
    #             'success': False,
    #             'error': f'输入文件不存在: {input_path}',
    #             'processing_time': 0
    #         }
        
    #     try:
    #         # 设置日志级别
    #         if verbose:
    #             self.logger.setLevel("DEBUG")
            
    #         # 确保输出目录存在
    #         ensure_dir(output_dir)
            
    #         # 获取文档名称
    #         if not doc_name:
    #             doc_name = Path(input_path).stem
            
    #         self.logger.info(f"开始处理单个文档: {input_path}")
    #         self.logger.info(f"文档名称: {doc_name}")
    #         self.logger.info(f"输出目录: {output_dir}")
            
    #         # 使用processor的process_documents方法处理单个文档
    #         self.logger.info("使用processor处理单个文档")
            
    #         # 临时更新分块配置（如果提供了覆盖参数）
    #         original_chunk_size = None
    #         original_chunk_overlap = None
    #         if chunk_size or chunk_overlap:
    #             original_chunk_size = self.llm_processor.chunk_size
    #             original_chunk_overlap = self.llm_processor.chunk_overlap
    #             if chunk_size:
    #                 self.llm_processor.chunk_size = chunk_size
    #             if chunk_overlap:
    #                 self.llm_processor.chunk_overlap = chunk_overlap
            
    #         try:
    #             # 使用processor的process_documents方法
    #             batch_results = self.llm_processor.process_documents(
    #                 [input_path], include_tables=include_tables
    #             )
                
    #             # 获取单个文档的处理结果
    #             doc_chunk_results = batch_results.get(input_path, [])
                
    #             # 转换结果格式
    #             all_results = []
    #             failed_chunks = []
                
    #             for i, (result, info) in enumerate(doc_chunk_results):
    #                 if info['success'] and result:
    #                     all_results.append(result)
    #                     self.logger.info(f"块 {i+1} 处理成功")
    #                 else:
    #                     failed_chunks.append({
    #                         'chunk_index': i,
    #                         'error': info.get('error', '未知错误'),
    #                         'processing_time': info.get('processing_time', 0)
    #                     })
    #                     self.logger.error(f"块 {i+1} 处理失败: {info.get('error')}")
                
    #             self.logger.info(f"共处理 {len(doc_chunk_results)} 个文本块，成功 {len(all_results)} 个")
                
    #             # 合并结果
    #             self.logger.info("合并处理结果...")
    #             merged_result = merge_knowledge_graph_results(all_results)
                
    #         finally:
    #             # 恢复原始配置
    #             if original_chunk_size is not None:
    #                 self.llm_processor.chunk_size = original_chunk_size
    #             if original_chunk_overlap is not None:
    #                 self.llm_processor.chunk_overlap = original_chunk_overlap
            
    #         # 保存结果
    #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #         safe_doc_name = sanitize_filename(doc_name)
    #         output_file = os.path.join(output_dir, f"{safe_doc_name}_{timestamp}_result.json")
    #         save_json(merged_result, output_file)
    #         self.logger.info(f"结果已保存: {output_file}")
            
    #         # 保存失败信息
    #         failed_file = None
    #         if failed_chunks:
    #             failed_file = os.path.join(output_dir, f"{safe_doc_name}_{timestamp}_failed.json")
    #             save_json(failed_chunks, failed_file)
    #             self.logger.warning(f"失败信息已保存: {failed_file}")
            
    #         # 生成统计报告
    #         stats = self.llm_processor.get_stats()
    #         processing_time = time.time() - start_time
            
    #         total_chunks = len(doc_chunk_results) if 'doc_chunk_results' in locals() else 0
            
    #         report = {
    #             'document_name': doc_name,
    #             'input_path': input_path,
    #             'processing_time': processing_time,
    #             'total_chunks': total_chunks,
    #             'successful_chunks': len(all_results),
    #             'failed_chunks': len(failed_chunks),
    #             'success_rate': (len(all_results) / total_chunks) * 100 if total_chunks > 0 else 0,
    #             'llm_stats': stats,
    #             'result_summary': {
    #                 'total_entities': len(merged_result.get('基础实体', [])),
    #                 'total_states': len(merged_result.get('状态实体', [])),
    #                 'total_relations': len(merged_result.get('状态关系', []))
    #             },
    #             'files': {
    #                 'result_file': output_file,
    #                 'failed_file': failed_file
    #             }
    #         }
            
    #         report_file = os.path.join(output_dir, f"{safe_doc_name}_{timestamp}_report.json")
    #         save_json(report, report_file)
            
    #         # 返回结果
    #         return {
    #             'success': True,
    #             'document_name': doc_name,
    #             'input_path': input_path,
    #             'output_directory': output_dir,
    #             'processing_time': processing_time,
    #             'chunks': {
    #                 'total': total_chunks,
    #                 'successful': len(all_results),
    #                 'failed': len(failed_chunks),
    #                 'success_rate': report['success_rate']
    #             },
    #             'entities': {
    #                 'total': report['result_summary']['total_entities'] + report['result_summary']['total_states'],
    #                 'basic_entities': report['result_summary']['total_entities'],
    #                 'state_entities': report['result_summary']['total_states']
    #             },
    #             'relations': {
    #                 'total': report['result_summary']['total_relations']
    #             },
    #             'files': {
    #                 'result_file': output_file,
    #                 'failed_file': failed_file,
    #                 'report_file': report_file
    #             },
    #             'llm_stats': stats
    #         }
            
    #     except Exception as e:
    #         self.logger.error(f"处理文档时发生错误: {e}")
    #         return {
    #             'success': False,
    #             'error': str(e),
    #             'processing_time': time.time() - start_time
    #         }