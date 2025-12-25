#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLMJson 配置驱动示例

展示如何使用配置文件驱动的方式进行信息提取。
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any

def load_environment():
    """加载环境变量配置"""
    print("🔧 加载环境配置...")
    
    # 从.env文件加载配置
    env_file = Path('.env')
    if env_file.exists():
        print("📄 从 .env 文件加载配置")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 移除可能的引号
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        os.environ[key] = value
                    except ValueError:
                        print(f"   ⚠️  跳过第{line_num}行 (格式错误): {line}")
    else:
        print("📄 未找到 .env 文件")
    
    # 设置默认值
    default_config = {
        'OPENAI_API_KEY': 'your-api-key-here',
        'OPENAI_BASE_URL': 'https://api.openai.com/v1',
        'OPENAI_MODEL': 'gpt-4o-mini'
    }
    
    for key, default_value in default_config.items():
        if key not in os.environ:
            os.environ[key] = default_value
    
    # 显示配置状态
    api_key = os.environ['OPENAI_API_KEY']
    if api_key and api_key != 'your-api-key-here':
        print(f"✅ API Key: {api_key[:10]}...{api_key[-4:]} (长度: {len(api_key)})")
    else:
        print(f"⚠️  API Key: 使用默认值，需要配置真实的API Key")
    
    print(f"✅ Base URL: {os.environ['OPENAI_BASE_URL']}")
    print(f"✅ Model: {os.environ['OPENAI_MODEL']}")

def process_with_config(config_path: str, text: str, doc_name: str = "示例文档"):
    """使用配置文件处理文本"""
    print(f"\n🔄 使用配置: {config_path}")
    print(f"📄 处理文档: {doc_name}")
    print(f"📝 文本长度: {len(text)} 字符")
    
    try:
        # 导入LLMJson
        from llmjson import ProcessorFactory
        
        # 创建处理器
        processor = ProcessorFactory.create_processor(config_path)
        print(f"✅ 处理器创建成功: {type(processor).__name__}")
        
        # 处理文本
        start_time = time.time()
        result, info = processor.process_chunk(text, doc_name)
        processing_time = time.time() - start_time
        
        if info['success']:
            print(f"✅ 处理成功! 耗时: {processing_time:.2f}秒")
            
            # 显示结果统计
            if result:
                for key, value in result.items():
                    if isinstance(value, list):
                        print(f"   {key}: {len(value)} 个")
            
            # 保存结果
            output_file = f"result_{Path(config_path).stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'config': config_path,
                    'processing_info': info,
                    'extracted_data': result
                }, f, ensure_ascii=False, indent=2)
            
            print(f"💾 结果已保存到: {output_file}")
            return True
            
        else:
            print(f"❌ 处理失败: {info.get('error', '未知错误')}")
            
            # 显示详细错误信息
            if info.get('error_type') == 'template_validation_error':
                print(f"🔍 验证错误: {info.get('validation_error', 'N/A')}")
            
            return False
            
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")
        return False

def main():
    """主函数"""
    print("🚀 LLMJson 配置驱动示例")
    print("="*50)
    
    # 加载环境配置
    load_environment()
    
    # 检查API配置
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key or api_key == 'your-api-key-here':
        print("\n⚠️  请配置有效的API Key后再运行")
        print("   1. 复制 .env.example 为 .env")
        print("   2. 在 .env 中填入真实的API配置")
        return False
    
    # 示例文本
    sample_texts = {
        "通用示例": "张三在苹果公司工作，公司位于北京市。李四是清华大学的教授。",
        "洪涝灾害示例": """
        2023年6月15日至7月10日，长江流域发生持续性强降雨过程，导致湖北省武汉市发生严重洪涝灾害。
        受灾人口达125.6万人，直接经济损失15.8亿元。三峡大坝在此次洪水过程中发挥了重要调节作用。
        """
    }
    
    # 可用的配置
    configs = [
        ("configs/universal_template.json", "通用信息提取"),
        ("configs/flood_disaster_complete.json", "洪涝灾害专用")
    ]
    
    print(f"\n📋 可用配置:")
    for i, (config_path, desc) in enumerate(configs, 1):
        if Path(config_path).exists():
            print(f"   {i}. {desc} ({config_path})")
        else:
            print(f"   {i}. {desc} ({config_path}) - ❌ 文件不存在")
    
    # 处理示例
    success_count = 0
    total_count = 0
    
    for config_path, config_desc in configs:
        if not Path(config_path).exists():
            continue
            
        print(f"\n{'='*50}")
        print(f"📊 测试配置: {config_desc}")
        
        # 选择合适的示例文本
        if "flood" in config_path.lower():
            text = sample_texts["洪涝灾害示例"]
            doc_name = "洪涝灾害报告"
        else:
            text = sample_texts["通用示例"]
            doc_name = "通用文档"
        
        total_count += 1
        if process_with_config(config_path, text.strip(), doc_name):
            success_count += 1
    
    # 显示总结
    print(f"\n{'='*50}")
    print(f"📊 处理总结: {success_count}/{total_count} 成功")
    
    if success_count > 0:
        print("✅ 配置驱动系统运行正常")
        print("\n📚 使用说明:")
        print("   1. 修改模板文件 (templates/*.yaml) 定义提取规则")
        print("   2. 修改配置文件 (configs/*.json) 设置处理参数")
        print("   3. 使用 ProcessorFactory.create_processor(config_path) 创建处理器")
    else:
        print("❌ 系统运行异常，请检查配置")
    
    return success_count > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)