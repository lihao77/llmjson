#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLMJson v2 简单CLI

基于factory.py的简洁命令行工具
"""

import sys
import argparse
from pathlib import Path

def create_config(output_path=None):
    """创建示例配置文件"""
    config_content = """{
  "template": {
    "config_path": "templates/universal.yaml"
  },
  "validator": {},
  "processor": {
    "api_key": "${OPENAI_API_KEY}",
    "base_url": "${OPENAI_BASE_URL}",
    "model": "${OPENAI_MODEL}",
    "temperature": 0.1,
    "max_tokens": 4000,
    "timeout": 60,
    "max_retries": 3,
    "retry_delay": 1.0
  }
}"""
    
    output_file = output_path or "config.json"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(config_content)
    
    print(f"[OK] 配置文件已创建: {output_file}")
    print("[TIP] 请设置环境变量: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL")

def process_text(config_path, text_file):
    """处理文本文件"""
    try:
        from llmjson import ProcessorFactory
        
        # 创建处理器
        processor = ProcessorFactory.create_processor(config_path)
        
        # 读取文本
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 处理
        result, info = processor.process_chunk(text, Path(text_file).name)
        
        if info['success']:
            # 保存结果
            output_file = f"result_{Path(text_file).stem}.json"
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] 处理完成: {output_file}")
        else:
            print(f"[ERROR] 处理失败: {info.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"[ERROR] {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="LLMJson v2 CLI")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # 创建配置
    config_parser = subparsers.add_parser('create-config', help='Create example config file')
    config_parser.add_argument('-o', '--output', help='Output config file path')
    
    # 处理文本
    process_parser = subparsers.add_parser('process', help='Process text file')
    process_parser.add_argument('text_file', help='Text file to process')
    process_parser.add_argument('-c', '--config', default='config.json', help='Config file')
    
    args = parser.parse_args()
    
    if args.command == 'create-config':
        create_config(getattr(args, 'output', None))
    elif args.command == 'process':
        process_text(args.config, args.text_file)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
