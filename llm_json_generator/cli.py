#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM JSON Generator 命令行接口

提供命令行工具来使用LLM JSON Generator包的功能。
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .processor import LLMProcessor
from .config import ConfigManager
from .utils import (
    ensure_dir, 
    save_json, 
    load_json,
    chunk_text,
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
from .run_mode import DocumentProcessor


@log_execution_time()
def create_config_command(args):
    """创建示例配置文件"""
    logger = create_logger_with_context({
        'command': 'create_config',
        'output': args.output or 'config.json'
    })
    
    logger.info("🔧 开始创建示例配置文件")
    
    config = ConfigManager()
    
    # 设置默认LLM配置
    config.llm_config.api_key = "your-openai-api-key-here"
    config.llm_config.model = "gpt-4o-mini"
    config.llm_config.temperature = 0.1
    config.llm_config.max_tokens = 4000
    config.llm_config.max_retries = 3
    config.llm_config.timeout = 60
    
    # 设置默认处理配置
    config.processing_config.chunk_size = 2000
    config.processing_config.chunk_overlap = 200
    config.processing_config.max_workers = 4
    config.processing_config.enable_parallel = True
    
    # 保存配置文件
    config_file = args.output or "config.json"
    config.save_to_file(config_file)
    
    logger.info(f"✅ 示例配置文件已创建: {config_file}")
    print(f"✅ 示例配置文件已创建: {config_file}")
    print("⚠️  请编辑配置文件，设置你的OpenAI API密钥")
    print(f"📝 编辑命令: notepad {config_file}" if os.name == 'nt' else f"📝 编辑命令: nano {config_file}")


@log_execution_time()
def process_text_command(args):
    """处理单个文本文件"""
    # 创建上下文日志器
    logger = create_logger_with_context({
        'command': 'process_text',
        'document_path': args.document_path,
        'output': args.output or 'output',
        'config': args.config or 'config.json'
    })
    
    # 检查输入文件
    if not os.path.exists(args.document_path):
        error_msg = f"输入文件不存在: {args.document_path}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        return 1
    
    # 检查配置文件
    config_file = args.config or "config.json"
    if not os.path.exists(config_file):
        error_msg = f"配置文件不存在: {config_file}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        print("💡 使用 'llm-json-generator create-config' 创建配置文件")
        return 1
    
    try:
        # 设置日志级别
        log_level = "DEBUG" if args.log else "INFO"
        main_logger = setup_logging(log_level)
        
        # 记录系统信息
        if args.log:
            log_system_info()
        
        logger.info("🤖 初始化文档处理器...")
        # 创建文档处理器
        print("🤖 初始化文档处理器...")
        processor = DocumentProcessor(config_file, args.template)
        
        # 确保输出目录存在
        output_dir = args.output or "output"
        
        # 处理单个文档
        logger.info(f"🚀 开始处理文档: {args.document_path}")
        print(f"🚀 开始处理文档: {args.document_path}")

        result = processor.process_single_document(
                document_path=args.document_path,
                base_output_dir=output_dir,
                include_tables=args.tables,
                generate_validation_report=args.validation
            )
        
        if result['success']:
            # 记录处理结果
            logger.info(f"✅ 文档处理成功，耗时: {result['processing_time']:.2f}秒")
            logger.info(f"📦 处理统计 - 总块数: {result['chunks']['total']}, "
                       f"成功: {result['chunks']['successful']}, "
                       f"失败: {result['chunks']['failed']}")
            
            # 输出摘要
            print("\n" + "="*50)
            print("📊 处理完成摘要")
            print("="*50)
            print(f"⏱️  处理耗时: {result['processing_time']:.2f}秒")
            print(f"📦 文本块数: {result['chunks']['total']}")
            print(f"✅ 成功处理: {result['chunks']['successful']}")
            print(f"❌ 处理失败: {result['chunks']['failed']}")
            print(f"📈 成功率: {result['chunks']['success_rate']:.1f}%")
            print(f"🏷️  提取实体: {result['entities']['total']}个 (基础: {result['entities']['basic_entities']}, 状态: {result['entities']['state_entities']})")
            print(f"🔗 提取关系: {result['relations']['total']}个")
            print(f"📁 输出目录: {result['output_directory']}")
            
            if result['chunks']['failed'] > 0:
                warning_msg = f"有 {result['chunks']['failed']} 个文本块处理失败"
                logger.warning(f"⚠️ {warning_msg}")
                print(f"\n⚠️  {warning_msg}，详情请查看失败报告")
                # 检查是否存在失败文件记录
                if result.get('files', {}).get('failed_file'):
                    print(f"📄 失败报告: {result['files']['failed_file']}")
                elif result.get('files', {}).get('chunks_results'):
                    print(f"📄 详细结果: {result['files']['chunks_results']}")
                        
            return 0
        else:
            error_msg = f"处理失败: {result['error']}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            return 1
        
    except Exception as e:
        error_msg = f"处理过程中发生错误: {e}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        if args.log:
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            traceback.print_exc()
        return 1


@log_execution_time()
def process_documents_command(args):
    """处理文档文件夹"""
    # 创建上下文日志器
    logger = create_logger_with_context({
        'command': 'process_documents',
        'folder_path': args.folder_path,
        'mode': args.mode or 'optimized',
        'output': args.output or 'output',
        'config': args.config or 'config.json'
    })
    
    # 检查配置文件
    config_file = args.config or "config.json"
    if not os.path.exists(config_file):
        error_msg = f"配置文件不存在: {config_file}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        print("💡 使用 'llm-json-generator create-config' 创建配置文件")
        return 1
    
    # 获取文件夹路径
    folder_path = args.folder_path
    
    # 验证文件夹存在性
    if not os.path.exists(folder_path):
        error_msg = f"文件夹不存在: {folder_path}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        return 1
    
    if not os.path.isdir(folder_path):
        error_msg = f"指定的路径不是文件夹: {folder_path}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        return 1
    
    logger.info(f"📁 准备处理文件夹: {folder_path}")
    print(f"📁 准备处理文件夹: {folder_path}")
    
    try:
        # 设置日志级别
        log_level = "DEBUG" if args.log else "INFO"
        main_logger = setup_logging(log_level)
        
        # 记录系统信息
        if args.log:
            log_system_info()
        
        logger.info("🤖 初始化文档处理器...")
        # 创建文档处理器
        print("🤖 初始化文档处理器...")
        processor = DocumentProcessor(config_file, args.template)
        
        # 确定处理模式
        mode = args.mode or "optimized"
        if mode not in ["batch", "optimized"]:
            error_msg = f"不支持的处理模式: {mode}"
            logger.error(f"❌ {error_msg}")
            print(f"❌ {error_msg}")
            print("💡 支持的模式: batch , optimized ")
            return 1
        
        mode_names = {
            "batch": "传统批量处理",
            "optimized": "优化流式处理"
        }
        
        logger.info(f"✅ 已选择处理模式: {mode_names[mode]}")
        print(f"\n✅ 已选择: {mode_names[mode]}")
        
        # 设置输出目录
        output_dir = args.output or "output"
        
        # 开始处理
        logger.info(f"🔄 开始{mode_names[mode]}...")
        print(f"\n🔄 开始{mode_names[mode]}...")
        
        # 使用计时上下文日志器
        timed_logger = create_timed_logger({
            'operation': f'{mode}_processing',
            'folder': folder_path
        })
        
        with timed_logger.time_context("document_processing"):
            if mode == "batch":
                results = processor.process_document_list_batch(
                    folder_path=folder_path,
                    base_output_dir=output_dir,
                    include_tables=args.tables,
                    generate_validation_report=args.validation
                )
            else:  # optimized
                results = processor.process_document_list_streaming_optimized(
                    folder_path=folder_path,
                    base_output_dir=output_dir,
                    include_tables=args.tables,
                    generate_validation_report=args.validation
                )
        
        # 记录处理结果
        success_rate = results['summary']['documents']['success_rate']
        logger.info(f"🎉 批量处理完成！成功率: {success_rate:.1f}%")
        logger.info(f"📁 输出目录: {results['processing_info']['output_directory']}")
        
        print(f"\n🎉 所有处理完成！")
        print(f"📁 输出目录: {results['processing_info']['output_directory']}")
        
        # 返回成功率作为退出码
        return 0 if success_rate > 80 else 1
        
    except Exception as e:
        error_msg = f"处理过程中发生错误: {e}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        if args.log:
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            traceback.print_exc()
        return 1


@log_execution_time()
def validate_command(args):
    """验证JSON数据"""
    from .validator import DataValidator
    
    # 创建上下文日志器
    logger = create_logger_with_context({
        'command': 'validate',
        'input': args.input,
        'output': args.output,
        'report': args.report
    })
    
    # 检查输入文件
    if not os.path.exists(args.input):
        error_msg = f"输入文件不存在: {args.input}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        return 1
    
    try:
        # 加载数据
        logger.info(f"📖 开始加载数据: {args.input}")
        print(f"📖 加载数据: {args.input}")
        data = load_json(args.input)
        logger.info(f"✅ 数据加载成功，记录数: {len(data) if isinstance(data, list) else 1}")
        
        # 创建验证器
        logger.info("🔍 创建数据验证器...")
        validator = DataValidator()
        
        # 验证数据
        logger.info("🔍 开始验证数据...")
        print("🔍 验证数据...")
        
        # 使用计时上下文日志器
        timed_logger = create_timed_logger({'operation': 'data_validation'})
        
        with timed_logger.time_context("validation"):
            validated_data, validation_report = validator.validate_data(data)
        
        # 获取验证报告
        summary = validator.get_validation_summary()
        full_report = validator.get_validation_report()
        
        # 记录验证结果
        logger.info(f"✅ 验证完成 - 成功率: {summary['success_rate']:.1f}%, "
                   f"错误: {summary['error_count']}, "
                   f"警告: {summary['warning_count']}, "
                   f"修复: {summary['correction_count']}")
        
        # 输出结果
        print("\n" + "="*40)
        print("📊 验证结果")
        print("="*40)
        print(f"✅ 验证成功率: {summary['success_rate']:.1f}%")
        print(f"❌ 错误数量: {summary['error_count']}")
        print(f"⚠️  警告数量: {summary['warning_count']}")
        print(f"🔧 修复数量: {summary['correction_count']}")
        
        if full_report.get('errors_deleted'):
            logger.info(f"❌ 发现 {len(full_report['errors_deleted'])} 个错误")
            print("\n❌ 错误详情:")
            for error in full_report['errors_deleted'][:5]:  # 只显示前5个错误
                print(f"  - {error}")
            if len(full_report['errors_deleted']) > 5:
                print(f"  ... 还有 {len(full_report['errors_deleted']) - 5} 个错误")
        
        # 保存验证后的数据
        if args.output:
            logger.info(f"💾 保存验证后的数据: {args.output}")
            save_json(validated_data, args.output)
            print(f"\n💾 验证后的数据已保存: {args.output}")
        
        # 保存验证报告
        if args.report:
            logger.info(f"📄 导出验证报告: {args.report}")
            validator.export_validation_report(args.report)
            print(f"📄 验证报告已保存: {args.report}")
        
        return 0 if summary['success_rate'] > 0.8 else 1
        
    except Exception as e:
        error_msg = f"验证过程中发生错误: {e}"
        logger.error(f"❌ {error_msg}")
        print(f"❌ {error_msg}")
        return 1


# merge_results函数已被merge_knowledge_graph_results替代


def check_help_request():
    """
    检查是否为帮助请求
    Check if this is a help request
    """
    help_flags = ['-h', '--help']

    # 检查参数中是否包含帮助标志
    for arg in sys.argv[1:]:
        if arg in help_flags:
            return True

        # 检查是否是子命令的帮助请求
        if arg in ['create-config', 'process', 'process-documents', 'validate']:
            # 检查下一个参数是否是帮助标志
            arg_index = sys.argv.index(arg)
            if arg_index + 1 < len(sys.argv) and sys.argv[arg_index + 1] in help_flags:
                return True

    # 没有参数也显示帮助
    return len(sys.argv) == 1


def conditional_log(logger, level, message):
    """
    条件日志记录函数
    Conditional logging function
    """
    if logger is not None:
        if level == 'info':
            logger.info(message)
        elif level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)


def main():
    """主函数 | Main function"""

    # 预解析参数，检查是否是帮助请求，避免生成日志文件
    is_help_request = check_help_request()

    # 只有在非帮助请求时才进行日志初始化
    main_logger = None
    if not is_help_request:
        main_logger = get_logger()
        main_logger.info("🚀 LLM JSON Generator CLI 启动")

    # 中英双语帮助信息
    description = """
LLM JSON Generator - 通过大语言模型生成知识图谱JSON数据
LLM JSON Generator - Generate knowledge graph JSON data using Large Language Models

主要功能 | Key Features:
• 文档处理: 支持 .txt 和 .docx 文档 | Document processing: Support .txt and .docx files
• 批量处理: 高效处理多个文档 | Batch processing: Efficient processing of multiple documents
• 数据验证: JSON数据验证和修复 | Data validation: JSON data validation and repair
• 并行处理: 多线程并行处理 | Parallel processing: Multi-threaded parallel processing
• 流式处理: 实时处理和输出 | Streaming processing: Real-time processing and output
"""

    examples = """
使用示例 | Usage Examples:

📋 配置管理 | Configuration Management:
  # 创建配置文件 | Create configuration file
  llm-json-generator create-config
  llm-json-generator create-config -o my_config.json

📄 单文档处理 | Single Document Processing:
  # 基础处理 | Basic processing
  llm-json-generator process document.txt
  llm-json-generator process document.docx

  # 自定义输出目录 | Custom output directory
  llm-json-generator process document.txt -o results/

  # 使用自定义配置 | Use custom configuration
  llm-json-generator process document.txt -c my_config.json

  # 包含表格和验证 | Include tables and validation
  llm-json-generator process document.txt --tables --validation

  # 启用详细日志 | Enable detailed logging
  llm-json-generator process document.txt -l

📁 批量文档处理 | Batch Document Processing:
  # 传统批量处理 | Traditional batch processing
  llm-json-generator process-documents /path/to/docs/ -m batch -o results/

  # 优化流式处理(推荐) | Optimized streaming processing (recommended)
  llm-json-generator process-documents /path/to/docs/ -m optimized -o results/

  # 完整参数示例 | Full parameter example
  llm-json-generator process-documents /path/to/docs/ \\
    -m optimized -o batch_results/ -c my_config.json --tables --validation -l

🔍 数据验证 | Data Validation:
  # 基础验证 | Basic validation
  llm-json-generator validate data.json

  # 保存验证后的数据和报告 | Save validated data and report
  llm-json-generator validate data.json -o validated_data.json -r validation_report.json

💡 高级用法 | Advanced Usage:
  # 使用自定义提示模板 | Use custom prompt template
  llm-json-generator process document.txt -t custom_template.json

  # 处理包含大量表格的文档 | Process documents with many tables
  llm-json-generator process-document folder/ --tables --validation -l

🎯 输出说明 | Output Description:
  • results/ - 处理结果目录 | Processing results directory
  • chunks_results.json - 文本块处理结果 | Text chunk processing results
  • failed_chunks.json - 失败的文本块 | Failed text chunks
  • validation_report.json - 数据验证报告 | Data validation report
  • knowledge_graph.json - 最终知识图谱 | Final knowledge graph

⚠️ 注意事项 | Important Notes:
  • 首次使用前请先创建配置文件 | Create configuration file before first use
  • 确保API密钥已正确配置 | Ensure API key is properly configured
  • 大文档建议使用流式处理 | Use streaming processing for large documents
  • 启用日志以获得详细错误信息 | Enable logging for detailed error information
"""

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令 | Available commands')

    # 创建配置命令
    config_help = """
创建示例配置文件 | Create example configuration file

此命令创建包含默认设置的配置文件，包含LLM配置和处理配置。
This command creates a configuration file with default settings, including LLM and processing configurations.

示例 | Example:
  llm-json-generator create-config
  llm-json-generator create-config -o /path/to/my_config.json
"""
    config_parser = subparsers.add_parser('create-config',
                                         help='创建示例配置文件 | Create example configuration file',
                                         description=config_help,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    config_parser.add_argument('-o', '--output',
                             help='配置文件输出路径 | Configuration file output path (默认: config.json | default: config.json)')
    config_parser.set_defaults(func=create_config_command)

    # 处理文本命令
    process_help = """
处理单个文本文件 | Process a single text document

处理单个文档(.txt或.docx)，提取实体和关系生成知识图谱。
Process a single document (.txt or .docx) to extract entities and relationships and generate a knowledge graph.

支持的格式 | Supported formats:
• 纯文本文件 (.txt) | Plain text files (.txt)
• Word文档 (.docx) | Word documents (.docx)

输出文件 | Output files:
• knowledge_graph.json - 最终知识图谱 | Final knowledge graph
• chunks_results.json - 文本块处理结果 | Text chunk processing results
• failed_chunks.json - 失败的文本块 | Failed text chunks (if any)
• validation_report.json - 验证报告 | Validation report (if --validation)

示例 | Examples:
  # 基础处理 | Basic processing
  llm-json-generator process document.txt

  # 自定义输出目录 | Custom output directory
  llm-json-generator process document.docx -o results/

  # 使用自定义配置 | Use custom configuration
  llm-json-generator process document.txt -c my_config.json

  # 包含表格和启用验证 | Include tables and enable validation
  llm-json-generator process document.txt --tables --validation

  # 启用详细日志 | Enable detailed logging
  llm-json-generator process document.txt -l
"""
    process_parser = subparsers.add_parser('process',
                                         help='处理单个文本文件 | Process a single text document',
                                         description=process_help,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    process_parser.add_argument('document_path',
                             help='文档路径 | Document file path (.txt or .docx)')
    process_parser.add_argument('-c', '--config',
                             help='配置文件路径 | Configuration file path (默认: config.json | default: config.json)')
    process_parser.add_argument('-o', '--output',
                             help='输出目录 | Output directory (默认: output | default: output)')
    process_parser.add_argument('-t', '--template',
                             help='提示模板文件路径 | Prompt template file path (默认: None | default: None)')
    process_parser.add_argument('--tables', action='store_true',
                             help='包含表格 | Include tables in processing')
    process_parser.add_argument('--validation', action='store_true',
                             help='开启数据验证 | Enable data validation')
    process_parser.add_argument('-l', '--log', action='store_true',
                             help='启用控制台日志输出 | Enable console logging output')
    process_parser.set_defaults(func=process_text_command)

    # 处理文档列表命令
    docs_help = """
批量处理文档文件夹 | Batch process document folder

处理文件夹中的所有文档，支持两种处理模式。
Process all documents in a folder with two processing modes available.

处理模式 | Processing Modes:
• batch: 传统批量处理，一次性加载所有文档 | Traditional batch processing, load all documents at once
  适合 | Suitable for: 少量文档，内存充足 | Few documents, sufficient memory
• optimized: 优化流式处理，分批流式处理 | Optimized streaming processing, batch streaming
  适合 | Suitable for: 大量文档，内存有限 | Many documents, limited memory (推荐 | recommended)

输出结构 | Output Structure:
results/
├── document1/
│   ├── knowledge_graph.json
│   ├── chunks_results.json
│   └── validation_report.json
└── document2/
    ├── knowledge_graph.json
    └── ...

示例 | Examples:
  # 传统批量处理 | Traditional batch processing
  llm-json-generator process-documents /path/to/docs/ -m batch -o results/

  # 优化流式处理 | Optimized streaming processing
  llm-json-generator process-documents /path/to/docs/ -m optimized -o results/

  # 完整参数 | Full parameters
  llm-json-generator process-documents /path/to/docs/ \\
    -m optimized -o batch_results/ -c my_config.json --tables --validation -l
"""
    docs_parser = subparsers.add_parser('process-documents',
                                      help='批量处理文档文件夹 | Batch process document folder',
                                      description=docs_help,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    docs_parser.add_argument('folder_path',
                           help='包含文档的文件夹路径 | Path to folder containing documents')
    docs_parser.add_argument('-c', '--config',
                           help='配置文件路径 | Configuration file path (默认: config.json | default: config.json)')
    docs_parser.add_argument('-o', '--output',
                           help='输出目录 | Output directory (默认: output | default: output)')
    docs_parser.add_argument('-m', '--mode', choices=['batch', 'optimized'],
                           help='处理模式 | Processing mode: batch (传统批量 | traditional batch), optimized (优化流式 | optimized streaming, 默认 | default)')
    docs_parser.add_argument('-t', '--template',
                           help='提示模板文件路径 | Prompt template file path (默认: None | default: None)')
    docs_parser.add_argument('--tables', action='store_true',
                           help='包含表格 | Include tables in processing')
    docs_parser.add_argument('--validation', action='store_true',
                           help='开启数据验证 | Enable data validation')
    docs_parser.add_argument('-l', '--log', action='store_true',
                           help='启用控制台日志输出 | Enable console logging output')
    docs_parser.set_defaults(func=process_documents_command)

    # 验证数据命令
    validate_help = """
验证JSON数据 | Validate JSON data

对JSON数据进行验证、修复和清理，生成详细的验证报告。
Validate, repair, and clean JSON data with detailed validation reports.

验证功能 | Validation Features:
• JSON格式验证 | JSON format validation
• 数据结构检查 | Data structure verification
• 错误自动修复 | Automatic error correction
• 数据完整性检查 | Data integrity checking
• 详细报告生成 | Detailed report generation

报告内容 | Report Content:
• 验证成功率 | Validation success rate
• 错误统计 | Error statistics
• 修复统计 | Repair statistics
• 错误详情 | Error details
• 警告信息 | Warning information

示例 | Examples:
  # 基础验证 | Basic validation
  llm-json-generator validate data.json

  # 保存验证后的数据 | Save validated data
  llm-json-generator validate data.json -o clean_data.json

  # 生成验证报告 | Generate validation report
  llm-json-generator validate data.json -r report.json

  # 保存数据和报告 | Save both data and report
  llm-json-generator validate data.json -o clean_data.json -r report.json
"""
    validate_parser = subparsers.add_parser('validate',
                                          help='验证JSON数据 | Validate JSON data',
                                          description=validate_help,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    validate_parser.add_argument('input',
                              help='输入JSON文件路径 | Input JSON file path')
    validate_parser.add_argument('-o', '--output',
                              help='验证后数据输出路径 | Validated data output path')
    validate_parser.add_argument('-r', '--report',
                              help='验证报告输出路径 | Validation report output path')
    validate_parser.set_defaults(func=validate_command)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        conditional_log(main_logger, 'info', "📖 显示帮助信息")
        parser.print_help()
        return 1
    
    # 执行命令
    try:
        conditional_log(main_logger, 'info', f"📝 执行命令: {args.command}")
        result = args.func(args)
        conditional_log(main_logger, 'info', f"✅ 命令执行完成，退出码: {result}")
        return result
    except KeyboardInterrupt:
        conditional_log(main_logger, 'info', "⏹️ 用户中断操作")
        print("\n⏹️  操作已取消")
        return 1
    except Exception as e:
        conditional_log(main_logger, 'error', f"❌ 发生未预期的错误: {e}")
        print(f"❌ 发生未预期的错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())