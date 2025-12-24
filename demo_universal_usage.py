#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLMJson 通用化使用演示

展示如何使用新的通用系统处理不同领域的信息抽取任务
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any

# 模拟导入（实际使用时从llmjson包导入）
# from llmjson import ProcessorFactory, ConfigurableTemplate, UniversalValidator

def create_demo_templates():
    """创建演示用的模板配置"""
    
    # 1. 通用知识图谱模板
    kg_template = {
        "name": "通用知识图谱提取",
        "description": "从文本中提取实体和关系",
        "version": "1.0",
        
        "output_schema": {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "type": {"type": "string"},
                            "name": {"type": "string"},
                            "properties": {"type": "object"}
                        },
                        "required": ["id", "type", "name"]
                    }
                },
                "relations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "target": {"type": "string"},
                            "type": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "required": ["source", "target", "type"]
                    }
                }
            },
            "required": ["entities", "relations"]
        },
        
        "entity_types": [
            {"name": "Person", "description": "人物实体"},
            {"name": "Organization", "description": "组织机构"},
            {"name": "Location", "description": "地理位置"},
            {"name": "Product", "description": "产品或服务"}
        ],
        
        "relation_types": [
            {"name": "works_for", "description": "工作关系"},
            {"name": "located_in", "description": "位置关系"},
            {"name": "founded_by", "description": "创立关系"},
            {"name": "produces", "description": "生产关系"}
        ],
        
        "system_prompt": """你是一个专业的知识图谱构建助手。请从给定文本中提取实体和关系。

实体类型：
{entity_types_description}

关系类型：
{relation_types_description}

输出格式：
{output_format_example}

要求：
1. 为每个实体分配唯一ID（格式：类型_序号，如Person_1）
2. 关系的source和target必须是已提取实体的ID
3. 只提取文本中明确提及的信息
4. 为关系分配置信度分数（0-1）""",
        
        "user_prompt": """请从以下文本中提取实体和关系：

文档：{doc_name}
内容：{chunk}

请返回JSON格式的结果。"""
    }
    
    # 2. 新闻事件提取模板
    news_template = {
        "name": "新闻事件提取",
        "description": "从新闻文本中提取事件信息",
        "version": "1.0",
        
        "output_schema": {
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "type": {"type": "string"},
                            "participants": {"type": "array", "items": {"type": "string"}},
                            "location": {"type": "string"},
                            "time": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["title", "type", "description"]
                    }
                }
            },
            "required": ["events"]
        },
        
        "event_types": [
            {"name": "政治事件", "description": "政府决策、选举、外交等"},
            {"name": "经济事件", "description": "市场变化、公司动态、贸易等"},
            {"name": "社会事件", "description": "社会现象、公共事件等"},
            {"name": "科技事件", "description": "技术发布、科研成果等"}
        ],
        
        "system_prompt": """你是一个新闻事件分析专家。请从新闻文本中提取重要事件信息。

事件类型：
{event_types_description}

输出格式：
{output_format_example}

提取要求：
1. 识别文本中的主要事件
2. 提取事件的关键要素：时间、地点、参与者
3. 对事件进行分类
4. 提供简洁的事件描述""",
        
        "user_prompt": """请分析以下新闻文本并提取事件信息：

新闻标题：{doc_name}
新闻内容：{chunk}

请返回JSON格式的事件信息。"""
    }
    
    # 3. 产品评论分析模板
    review_template = {
        "name": "产品评论分析",
        "description": "从产品评论中提取关键信息和情感",
        "version": "1.0",
        
        "output_schema": {
            "type": "object",
            "properties": {
                "product_aspects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "aspect": {"type": "string"},
                            "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                            "opinion": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "required": ["aspect", "sentiment", "opinion"]
                    }
                },
                "overall_rating": {"type": "integer", "minimum": 1, "maximum": 5},
                "summary": {"type": "string"}
            },
            "required": ["product_aspects", "overall_rating", "summary"]
        },
        
        "aspects": [
            {"name": "质量", "description": "产品质量相关评价"},
            {"name": "价格", "description": "价格性价比相关评价"},
            {"name": "服务", "description": "客户服务相关评价"},
            {"name": "物流", "description": "配送物流相关评价"},
            {"name": "外观", "description": "产品外观设计相关评价"}
        ],
        
        "system_prompt": """你是一个产品评论分析专家。请从用户评论中提取产品各方面的评价信息。

分析维度：
{aspects_description}

情感分类：
- positive: 正面评价
- negative: 负面评价  
- neutral: 中性评价

输出格式：
{output_format_example}

分析要求：
1. 识别评论中涉及的产品方面
2. 判断每个方面的情感倾向
3. 提取具体的评价意见
4. 给出整体评分（1-5分）
5. 生成评论摘要""",
        
        "user_prompt": """请分析以下产品评论：

产品：{doc_name}
评论内容：{chunk}

请返回JSON格式的分析结果。"""
    }
    
    return {
        "knowledge_graph": kg_template,
        "news_events": news_template,
        "product_review": review_template
    }

def create_processor_configs():
    """创建处理器配置"""
    
    configs = {}
    
    # 通用知识图谱配置
    configs["knowledge_graph"] = {
        "template": {
            "config_path": "templates/knowledge_graph.yaml"
        },
        "validator": {
            "rules": [
                {
                    "type": "entity_deduplication",
                    "params": {"similarity_threshold": 0.8}
                },
                {
                    "type": "relation_validation", 
                    "params": {"check_entity_existence": True}
                }
            ]
        },
        "processor": {
            "api_key": "${OPENAI_API_KEY}",
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 4000
        }
    }
    
    # 新闻事件提取配置
    configs["news_events"] = {
        "template": {
            "config_path": "templates/news_events.yaml"
        },
        "validator": {
            "rules": [
                {
                    "type": "time_format_validation",
                    "params": {"auto_correct": True}
                }
            ]
        },
        "processor": {
            "api_key": "${OPENAI_API_KEY}",
            "model": "gpt-4o-mini", 
            "temperature": 0.2,
            "max_tokens": 3000
        }
    }
    
    # 产品评论分析配置
    configs["product_review"] = {
        "template": {
            "config_path": "templates/product_review.yaml"
        },
        "validator": {
            "rules": [
                {
                    "type": "sentiment_consistency",
                    "params": {"check_rating_alignment": True}
                }
            ]
        },
        "processor": {
            "api_key": "${OPENAI_API_KEY}",
            "model": "gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 2000
        }
    }
    
    return configs

def demo_usage_scenarios():
    """演示不同使用场景"""
    
    print("=== LLMJson 通用化使用演示 ===\n")
    
    # 创建模板和配置文件
    templates = create_demo_templates()
    configs = create_processor_configs()
    
    # 创建目录
    Path("templates").mkdir(exist_ok=True)
    Path("configs").mkdir(exist_ok=True)
    
    # 保存模板文件
    for name, template in templates.items():
        template_path = f"templates/{name}.yaml"
        with open(template_path, 'w', encoding='utf-8') as f:
            yaml.dump(template, f, ensure_ascii=False, indent=2)
        print(f"✅ 创建模板: {template_path}")
    
    # 保存配置文件
    for name, config in configs.items():
        config_path = f"configs/{name}.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 创建配置: {config_path}")
    
    print("\n=== 使用示例 ===\n")
    
    # 场景1：知识图谱提取
    print("1. 知识图谱提取示例：")
    print("```python")
    print("from llmjson import ProcessorFactory")
    print("")
    print("# 加载知识图谱处理器")
    print("processor = ProcessorFactory.create_processor('configs/knowledge_graph.json')")
    print("")
    print("# 处理文本")
    print("text = '苹果公司是一家位于加利福尼亚州的科技公司，由史蒂夫·乔布斯创立。'")
    print("result, info = processor.process_chunk(text, 'company_info.txt')")
    print("")
    print("if info['success']:")
    print("    print('提取的实体：', result['entities'])")
    print("    print('提取的关系：', result['relations'])")
    print("```")
    print("")
    
    # 场景2：新闻事件提取
    print("2. 新闻事件提取示例：")
    print("```python")
    print("# 加载新闻事件处理器")
    print("news_processor = ProcessorFactory.create_processor('configs/news_events.json')")
    print("")
    print("# 处理新闻文本")
    print("news_text = '特斯拉公司今日宣布在上海建设新的超级工厂，预计明年投产。'")
    print("result, info = news_processor.process_chunk(news_text, '科技新闻')")
    print("")
    print("if info['success']:")
    print("    for event in result['events']:")
    print("        print(f'事件：{event[\"title\"]} - {event[\"type\"]}')")
    print("```")
    print("")
    
    # 场景3：产品评论分析
    print("3. 产品评论分析示例：")
    print("```python")
    print("# 加载评论分析处理器")
    print("review_processor = ProcessorFactory.create_processor('configs/product_review.json')")
    print("")
    print("# 处理评论文本")
    print("review_text = '这款手机质量很好，拍照效果不错，但是价格有点贵。'")
    print("result, info = review_processor.process_chunk(review_text, 'iPhone 15')")
    print("")
    print("if info['success']:")
    print("    print(f'整体评分：{result[\"overall_rating\"]}/5')")
    print("    for aspect in result['product_aspects']:")
    print("        print(f'{aspect[\"aspect\"]}: {aspect[\"sentiment\"]} - {aspect[\"opinion\"]}')")
    print("```")
    print("")
    
    # 场景4：自定义模板
    print("4. 创建自定义模板：")
    print("```yaml")
    print("# templates/custom_domain.yaml")
    print("name: '自定义领域提取'")
    print("description: '针对特定领域的信息提取'")
    print("")
    print("output_schema:")
    print("  type: 'object'")
    print("  properties:")
    print("    # 定义你的输出结构")
    print("    custom_entities:")
    print("      type: 'array'")
    print("      items:")
    print("        type: 'object'")
    print("        properties:")
    print("          name: {type: 'string'}")
    print("          category: {type: 'string'}")
    print("")
    print("system_prompt: |")
    print("  你是一个{domain}领域的专家...")
    print("")
    print("user_prompt: |")
    print("  请从以下{domain}文本中提取信息：")
    print("  {chunk}")
    print("```")
    print("")
    
    print("=== 优势对比 ===\n")
    
    print("原有系统（专用）：")
    print("❌ 只能处理洪涝灾害领域")
    print("❌ 模板和验证规则硬编码")
    print("❌ 扩展新领域需要修改源码")
    print("❌ 难以复用和分享")
    print("")
    
    print("新系统（通用）：")
    print("✅ 支持任意领域的信息抽取")
    print("✅ 配置驱动，无需修改代码")
    print("✅ 模板可复用和分享")
    print("✅ 插件化验证规则")
    print("✅ 向后兼容，平滑迁移")
    print("✅ 支持多种输出格式")
    print("")
    
    print("=== 下一步 ===\n")
    print("1. 安装依赖：pip install jsonschema pyyaml")
    print("2. 设置API密钥：export OPENAI_API_KEY='your-key'")
    print("3. 运行示例：python demo_universal_usage.py")
    print("4. 创建自己的模板和配置")
    print("5. 享受通用化的信息抽取能力！")

if __name__ == "__main__":
    demo_usage_scenarios()