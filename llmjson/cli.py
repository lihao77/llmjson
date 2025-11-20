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
        print("💡 使用 'llmjson create-config' 创建配置文件")
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
        print("💡 使用 'llmjson create-config' 创建配置文件")
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

    # Professional bilingual help information
    description = """
LLM JSON Generator - Extract structured knowledge graphs from documents using LLMs
基于大语言模型从文档中提取结构化知识图谱

FEATURES:
  • Document Processing    Process .txt and .docx files with intelligent chunking
  • Batch Operations       Efficient parallel processing of multiple documents
  • Data Validation        Automatic JSON validation, repair, and quality assurance
  • Flexible Configuration Environment variables, config files, and CLI options
  • Production Ready       Retry logic, error handling, and comprehensive logging

主要功能：
  • 文档处理    支持 .txt 和 .docx 格式，智能分块处理
  • 批量操作    多文档并行处理，高效处理大规模任务
  • 数据验证    自动 JSON 验证、修复和质量保证
  • 灵活配置    支持环境变量、配置文件和命令行参数
  • 生产就绪    重试逻辑、错误处理和完整日志记录
"""

    examples = """
EXAMPLES:

  Configuration Setup:
    $ llmjson create-config                    # Create default config.json
    $ llmjson create-config -o my_config.json  # Custom config path

  Single Document Processing:
    $ llmjson process document.txt             # Process with default config
    $ llmjson process report.docx -o output/   # Custom output directory
    $ llmjson process doc.txt -c config.json   # Specify config file
    $ llmjson process data.docx --tables       # Include table extraction
    $ llmjson process file.txt --validation -l # Enable validation and logging

  Batch Document Processing:
    $ llmjson process-documents ./docs/                    # Process all documents
    $ llmjson process-documents ./docs/ -m optimized       # Streaming mode (recommended)
    $ llmjson process-documents ./docs/ -m batch           # Traditional batch mode
    $ llmjson process-documents ./docs/ -c config.json \\
        --tables --validation -o results/                  # Full options

  Data Validation:
    $ llmjson validate data.json                           # Basic validation
    $ llmjson validate data.json -o clean.json             # Save cleaned data
    $ llmjson validate data.json -r report.json            # Generate report
    $ llmjson validate data.json -o clean.json -r report.json  # Both outputs

  Advanced Usage:
    $ llmjson process doc.txt -t custom_template.json      # Custom prompt template
    $ llmjson process doc.txt -c prod_config.json          # Production configuration
    $ export OPENAI_API_KEY="sk-..."                       # Set API key via env
    $ llmjson process doc.txt -l 2>&1 | tee process.log    # Capture detailed logs

OUTPUT STRUCTURE:
  output/
  ├── document_name/
  │   ├── knowledge_graph.json       Final extracted knowledge graph
  │   ├── chunks_results.json        Per-chunk processing results
  │   ├── failed_chunks.json         Failed chunks (if any)
  │   └── validation_report.json     Data quality report (if --validation)

WORKFLOW:
  1. Create configuration file with API credentials
  2. Process documents to extract knowledge graph
  3. Validate and clean extracted data
  4. Use validated JSON for downstream applications

TIPS:
  • Store API key in environment variable for security: OPENAI_API_KEY
  • Use 'optimized' mode for large document batches (lower memory usage)
  • Enable --validation to ensure data quality
  • Use -l flag when troubleshooting issues

示例用法：

  配置设置：
    $ llmjson create-config                    # 创建默认 config.json
    $ llmjson create-config -o my_config.json  # 自定义配置路径

  单文档处理：
    $ llmjson process document.txt             # 使用默认配置处理
    $ llmjson process report.docx -o output/   # 指定输出目录
    $ llmjson process doc.txt -c config.json   # 指定配置文件
    $ llmjson process data.docx --tables       # 提取表格数据
    $ llmjson process file.txt --validation -l # 启用验证和日志

  批量文档处理：
    $ llmjson process-documents ./docs/                    # 处理所有文档
    $ llmjson process-documents ./docs/ -m optimized       # 流式模式（推荐）
    $ llmjson process-documents ./docs/ -m batch           # 传统批量模式
    $ llmjson process-documents ./docs/ -c config.json \\
        --tables --validation -o results/                  # 完整选项

  数据验证：
    $ llmjson validate data.json                           # 基础验证
    $ llmjson validate data.json -o clean.json             # 保存清理数据
    $ llmjson validate data.json -r report.json            # 生成报告
    $ llmjson validate data.json -o clean.json -r report.json  # 同时输出

  高级用法：
    $ llmjson process doc.txt -t custom_template.json      # 自定义提示模板
    $ llmjson process doc.txt -c prod_config.json          # 生产环境配置
    $ export OPENAI_API_KEY="sk-..."                       # 通过环境变量设置密钥
    $ llmjson process doc.txt -l 2>&1 | tee process.log    # 捕获详细日志

输出结构：
  output/
  ├── document_name/
  │   ├── knowledge_graph.json       最终提取的知识图谱
  │   ├── chunks_results.json        每个文本块的处理结果
  │   ├── failed_chunks.json         失败的文本块（如有）
  │   └── validation_report.json     数据质量报告（如启用 --validation）

工作流程：
  1. 创建包含 API 凭证的配置文件
  2. 处理文档以提取知识图谱
  3. 验证和清理提取的数据
  4. 将验证后的 JSON 用于下游应用

使用技巧：
  • 将 API 密钥存储在环境变量中以提高安全性：OPENAI_API_KEY
  • 对大型文档批次使用 'optimized' 模式（降低内存使用）
  • 启用 --validation 以确保数据质量
  • 排查问题时使用 -l 标志
"""

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=examples
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        title='COMMANDS',
        description='Available commands for document processing and validation',
        metavar='{create-config,process,process-documents,validate}',
        help='command to execute (use "llmjson <command> -h" for details)'
    )

    # Create configuration command
    config_help = """
Generate a configuration file with default LLM and processing settings.

This command creates a JSON configuration file containing:
  • LLM settings (API key, model, temperature, tokens, retry logic)
  • Processing settings (chunk size, overlap, parallel workers)

The generated file can be customized and used with -c/--config option.

USAGE:
  llmjson create-config [-o OUTPUT]

EXAMPLES:
  $ llmjson create-config                    # Creates config.json in current directory
  $ llmjson create-config -o app/config.json # Custom output path

NOTE: Remember to edit the file and set your actual API key before use.

生成包含默认 LLM 和处理设置的配置文件。

此命令创建包含以下内容的 JSON 配置文件：
  • LLM 设置（API 密钥、模型、温度、令牌数、重试逻辑）
  • 处理设置（分块大小、重叠、并行工作线程数）

生成的文件可以自定义并通过 -c/--config 选项使用。

用法：
  llmjson create-config [-o 输出路径]

示例：
  $ llmjson create-config                    # 在当前目录创建 config.json
  $ llmjson create-config -o app/config.json # 自定义输出路径

注意：请记得编辑文件并设置实际的 API 密钥后再使用。
"""
    config_parser = subparsers.add_parser('create-config',
                                         help='Generate configuration file with default settings',
                                         description=config_help,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    config_parser.add_argument('-o', '--output',
                             metavar='FILE',
                             help='output path for configuration file (default: config.json)')
    config_parser.set_defaults(func=create_config_command)

    # Process document command
    process_help = """
Extract entities and relationships from a document to build a knowledge graph.

Processes a single document (.txt or .docx), automatically chunks the text, sends
each chunk to the LLM for entity/relationship extraction, and aggregates results
into a unified knowledge graph.

SUPPORTED FORMATS:
  • Plain text files (.txt)
  • Microsoft Word documents (.docx)

OUTPUT FILES:
  knowledge_graph.json       Final aggregated knowledge graph
  chunks_results.json        Detailed per-chunk processing results
  failed_chunks.json         Information about failed chunks (if any)
  validation_report.json     Data quality report (with --validation flag)

USAGE:
  llmjson process DOCUMENT [OPTIONS]

OPTIONS:
  -c, --config FILE         Configuration file path (default: config.json)
  -o, --output DIR          Output directory (default: output)
  -t, --template FILE       Custom prompt template file
  --tables                  Extract and process table content
  --validation              Validate and clean extracted data
  -l, --log                 Enable detailed console logging

EXAMPLES:
  $ llmjson process document.txt                      # Basic processing
  $ llmjson process report.docx -o results/           # Custom output directory
  $ llmjson process data.txt -c custom_config.json    # Custom configuration
  $ llmjson process tables.docx --tables --validation # Extract tables with validation
  $ llmjson process debug.txt -l                      # Enable detailed logging

处理单个文档以提取实体和关系，构建知识图谱。

处理单个文档（.txt 或 .docx），自动分块文本，将每个块发送到 LLM 进行
实体/关系提取，并将结果聚合为统一的知识图谱。

支持格式：
  • 纯文本文件 (.txt)
  • Microsoft Word 文档 (.docx)

输出文件：
  knowledge_graph.json       最终聚合的知识图谱
  chunks_results.json        详细的每块处理结果
  failed_chunks.json         失败块的信息（如有）
  validation_report.json     数据质量报告（使用 --validation 标志）

用法：
  llmjson process 文档 [选项]

选项：
  -c, --config FILE         配置文件路径（默认：config.json）
  -o, --output DIR          输出目录（默认：output）
  -t, --template FILE       自定义提示模板文件
  --tables                  提取和处理表格内容
  --validation              验证和清理提取的数据
  -l, --log                 启用详细的控制台日志

示例：
  $ llmjson process document.txt                      # 基础处理
  $ llmjson process report.docx -o results/           # 自定义输出目录
  $ llmjson process data.txt -c custom_config.json    # 自定义配置
  $ llmjson process tables.docx --tables --validation # 提取表格并验证
  $ llmjson process debug.txt -l                      # 启用详细日志
"""
    process_parser = subparsers.add_parser('process',
                                         help='Process a single document to extract knowledge graph',
                                         description=process_help,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    process_parser.add_argument('document_path',
                             metavar='DOCUMENT',
                             help='path to document file (.txt or .docx)')
    process_parser.add_argument('-c', '--config',
                             metavar='FILE',
                             help='configuration file path (default: config.json)')
    process_parser.add_argument('-o', '--output',
                             metavar='DIR',
                             help='output directory (default: output)')
    process_parser.add_argument('-t', '--template',
                             metavar='FILE',
                             help='custom prompt template file')
    process_parser.add_argument('--tables', action='store_true',
                             help='extract and process tables from documents')
    process_parser.add_argument('--validation', action='store_true',
                             help='validate and clean extracted data')
    process_parser.add_argument('-l', '--log', action='store_true',
                             help='enable detailed console logging')
    process_parser.set_defaults(func=process_text_command)

    # Process documents batch command
    docs_help = """
Batch process all documents in a folder with configurable processing modes.

Recursively discovers and processes all .txt and .docx files in the specified
folder. Supports two processing modes optimized for different scenarios.

PROCESSING MODES:
  batch                     Load all documents into memory, process in parallel
                            Best for: Small to medium datasets, ample RAM
  
  optimized (recommended)   Stream documents with batched processing
                            Best for: Large datasets, memory constraints
                            Lower memory footprint, better scalability

OUTPUT STRUCTURE:
  results/
  ├── document1/
  │   ├── knowledge_graph.json      Extracted knowledge graph
  │   ├── chunks_results.json       Per-chunk details
  │   └── validation_report.json    Quality report (if --validation)
  ├── document2/
  │   └── ...
  └── processing_summary.json       Overall statistics

USAGE:
  llmjson process-documents FOLDER [OPTIONS]

OPTIONS:
  -c, --config FILE         Configuration file path (default: config.json)
  -o, --output DIR          Output directory (default: output)
  -m, --mode MODE           Processing mode: batch or optimized (default: optimized)
  -t, --template FILE       Custom prompt template file
  --tables                  Extract and process table content
  --validation              Validate and clean extracted data
  -l, --log                 Enable detailed console logging

EXAMPLES:
  $ llmjson process-documents ./documents/                    # Process with defaults
  $ llmjson process-documents ./docs/ -m batch                # Traditional batch mode
  $ llmjson process-documents ./docs/ -m optimized -o out/    # Streaming mode
  $ llmjson process-documents ./docs/ --tables --validation   # Extract tables with validation
  $ llmjson process-documents ./docs/ -c prod_config.json -l  # Production config with logging

批量处理文件夹中的所有文档，支持可配置的处理模式。

递归发现并处理指定文件夹中的所有 .txt 和 .docx 文件。支持针对不同场景
优化的两种处理模式。

处理模式：
  batch                     将所有文档加载到内存中，并行处理
                            最适合：中小型数据集，充足的 RAM
  
  optimized（推荐）         流式处理文档，分批处理
                            最适合：大型数据集，内存受限
                            更低的内存占用，更好的可扩展性

输出结构：
  results/
  ├── document1/
  │   ├── knowledge_graph.json      提取的知识图谱
  │   ├── chunks_results.json       每块详细信息
  │   └── validation_report.json    质量报告（如 --validation）
  ├── document2/
  │   └── ...
  └── processing_summary.json       总体统计

用法：
  llmjson process-documents 文件夹 [选项]

选项：
  -c, --config FILE         配置文件路径（默认：config.json）
  -o, --output DIR          输出目录（默认：output）
  -m, --mode MODE           处理模式：batch 或 optimized（默认：optimized）
  -t, --template FILE       自定义提示模板文件
  --tables                  提取和处理表格内容
  --validation              验证和清理提取的数据
  -l, --log                 启用详细的控制台日志

示例：
  $ llmjson process-documents ./documents/                    # 使用默认设置处理
  $ llmjson process-documents ./docs/ -m batch                # 传统批量模式
  $ llmjson process-documents ./docs/ -m optimized -o out/    # 流式模式
  $ llmjson process-documents ./docs/ --tables --validation   # 提取表格并验证
  $ llmjson process-documents ./docs/ -c prod_config.json -l  # 生产配置并记录日志
"""
    docs_parser = subparsers.add_parser('process-documents',
                                      help='Batch process all documents in a folder',
                                      description=docs_help,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    docs_parser.add_argument('folder_path',
                           metavar='FOLDER',
                           help='path to folder containing documents')
    docs_parser.add_argument('-c', '--config',
                           metavar='FILE',
                           help='configuration file path (default: config.json)')
    docs_parser.add_argument('-o', '--output',
                           metavar='DIR',
                           help='output directory (default: output)')
    docs_parser.add_argument('-m', '--mode', choices=['batch', 'optimized'],
                           metavar='MODE',
                           help='processing mode: batch or optimized (default: optimized)')
    docs_parser.add_argument('-t', '--template',
                           metavar='FILE',
                           help='custom prompt template file')
    docs_parser.add_argument('--tables', action='store_true',
                           help='extract and process tables from documents')
    docs_parser.add_argument('--validation', action='store_true',
                           help='validate and clean extracted data')
    docs_parser.add_argument('-l', '--log', action='store_true',
                           help='enable detailed console logging')
    docs_parser.set_defaults(func=process_documents_command)

    # 验证数据命令
    validate_help = """
Validate, repair, and clean JSON knowledge graph data with detailed reporting.

Performs comprehensive validation of extracted knowledge graph data, including
schema validation, data integrity checks, automatic error correction, and
generation of detailed quality reports.

VALIDATION FEATURES:
  • JSON format validation and repair
  • Knowledge graph schema verification
  • Entity and relationship validation
  • Automatic correction of common errors
  • Data completeness and consistency checks
  • Duplicate detection and removal

REPORT CONTENT:
  • Validation success rate and overall quality score
  • Error and warning counts with detailed descriptions
  • Automatic corrections applied
  • Data statistics (entities, relationships, etc.)
  • Recommendations for manual review

USAGE:
  llmjson validate INPUT [OPTIONS]

OPTIONS:
  -o, --output FILE         Save validated and cleaned data
  -r, --report FILE         Generate detailed validation report

EXAMPLES:
  $ llmjson validate data.json                              # Basic validation
  $ llmjson validate data.json -o clean.json                # Save cleaned data
  $ llmjson validate data.json -r report.json               # Generate report only
  $ llmjson validate data.json -o clean.json -r report.json # Save both outputs

TYPICAL WORKFLOW:
  1. Process documents:    llmjson process-documents ./docs/
  2. Validate results:     llmjson validate output/*/knowledge_graph.json -o validated.json
  3. Review report:        Check validation metrics and warnings
  4. Use validated data:   Downstream applications use validated.json

验证、修复和清理 JSON 知识图谱数据，并生成详细报告。

对提取的知识图谱数据进行全面验证，包括模式验证、数据完整性检查、
自动错误修正和详细质量报告生成。

验证功能：
  • JSON 格式验证和修复
  • 知识图谱模式验证
  • 实体和关系验证
  • 常见错误的自动修正
  • 数据完整性和一致性检查
  • 重复检测和删除

报告内容：
  • 验证成功率和整体质量分数
  • 错误和警告计数及详细描述
  • 应用的自动修正
  • 数据统计（实体、关系等）
  • 人工审查建议

用法：
  llmjson validate 输入 [选项]

选项：
  -o, --output FILE         保存验证和清理后的数据
  -r, --report FILE         生成详细验证报告

示例：
  $ llmjson validate data.json                              # 基础验证
  $ llmjson validate data.json -o clean.json                # 保存清理数据
  $ llmjson validate data.json -r report.json               # 仅生成报告
  $ llmjson validate data.json -o clean.json -r report.json # 保存两个输出

典型工作流程：
  1. 处理文档：       llmjson process-documents ./docs/
  2. 验证结果：       llmjson validate output/*/knowledge_graph.json -o validated.json
  3. 审查报告：       检查验证指标和警告
  4. 使用验证数据：   下游应用使用 validated.json
"""
    validate_parser = subparsers.add_parser('validate',
                                          help='Validate and clean JSON knowledge graph data',
                                          description=validate_help,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    validate_parser.add_argument('input',
                              metavar='INPUT',
                              help='input JSON file to validate')
    validate_parser.add_argument('-o', '--output',
                              metavar='FILE',
                              help='save validated and cleaned data to file')
    validate_parser.add_argument('-r', '--report',
                              metavar='FILE',
                              help='generate detailed validation report')
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