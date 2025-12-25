"""
处理器工厂

根据配置文件创建不同类型的处理器。
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from .processors.universal import UniversalProcessor
from .templates.base import ConfigurableTemplate
from .templates.legacy import LegacyFloodTemplate
from .validators.universal import UniversalValidator, LegacyValidatorAdapter
from .validators.rules.common import EntityDeduplicationRule, RelationValidationRule, TimeFormatValidationRule
from .validators.rules.flood_disaster import FloodDisasterValidationRules


class ProcessorFactory:
    """处理器工厂，根据配置创建处理器"""
    
    @staticmethod
    def create_processor(config_path: str) -> UniversalProcessor:
        """根据配置文件创建处理器
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置好的处理器实例
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return ProcessorFactory.create_from_config(config)
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> UniversalProcessor:
        """根据配置字典创建处理器
        
        Args:
            config: 配置字典
            
        Returns:
            配置好的处理器实例
        """
        # 1. 创建模板
        template = ProcessorFactory._create_template(config.get('template', {}))
        
        # 2. 创建验证器
        validator = ProcessorFactory._create_validator(config.get('validator', {}), template)
        
        # 3. 处理器配置
        processor_config = config.get('processor', {})
        
        # 环境变量替换
        processor_config = ProcessorFactory._resolve_env_vars(processor_config)
        
        # 4. 创建处理器
        return UniversalProcessor(
            template=template,
            validator=validator,
            **processor_config
        )
    
    @staticmethod
    def create_flood_disaster_processor(**kwargs) -> UniversalProcessor:
        """创建洪涝灾害专用处理器（快捷方法）
        
        Args:
            **kwargs: 处理器参数
            
        Returns:
            洪涝灾害处理器实例
        """
        template = LegacyFloodTemplate()
        validator = LegacyValidatorAdapter()
        
        return UniversalProcessor(
            template=template,
            validator=validator,
            **kwargs
        )
    
    @staticmethod
    def _create_template(template_config: Dict[str, Any]):
        """创建模板实例"""
        if 'config_path' in template_config:
            # 配置文件模板
            config_path = template_config['config_path']
            if not Path(config_path).exists():
                raise FileNotFoundError(f"模板配置文件不存在: {config_path}")
            return ConfigurableTemplate(config_path)
        
        elif template_config.get('type') == 'flood_disaster':
            # 洪涝灾害模板
            return LegacyFloodTemplate()
        
        else:
            # 默认使用洪涝灾害模板
            return LegacyFloodTemplate()
    
    @staticmethod
    def _create_validator(validator_config: Dict[str, Any], template) -> Optional[UniversalValidator]:
        """创建验证器实例"""
        if not validator_config:
            return None
        
        if validator_config.get('type') == 'legacy':
            # 使用原有验证器
            return LegacyValidatorAdapter()
        
        elif validator_config.get('type') == 'universal':
            # 通用验证器
            schema = template.schema if hasattr(template, 'schema') else {}
            custom_rules = ProcessorFactory._create_validation_rules(
                validator_config.get('rules', [])
            )
            return UniversalValidator(schema, custom_rules)
        
        else:
            # 默认根据模板类型选择验证器
            if isinstance(template, LegacyFloodTemplate):
                return LegacyValidatorAdapter()
            else:
                schema = template.schema if hasattr(template, 'schema') else {}
                return UniversalValidator(schema, [])
    
    @staticmethod
    def _create_validation_rules(rules_config: List[Dict[str, Any]]) -> List:
        """创建验证规则列表"""
        rules = []
        
        for rule_config in rules_config:
            rule_type = rule_config.get('type')
            rule_params = rule_config.get('params', {})
            
            if rule_type == 'entity_deduplication':
                rules.append(EntityDeduplicationRule(**rule_params))
            
            elif rule_type == 'relation_validation':
                rules.append(RelationValidationRule(**rule_params))
            
            elif rule_type == 'time_format_validation':
                rules.append(TimeFormatValidationRule(**rule_params))
            
            elif rule_type == 'flood_disaster_validation':
                # 添加所有洪涝灾害验证规则
                rules.extend(FloodDisasterValidationRules.get_all_rules())
            
            # 可以继续添加其他规则类型
        
        return rules
    
    @staticmethod
    def _resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置中的环境变量"""
        resolved_config = {}
        
        for key, value in config.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # 环境变量格式: ${VAR_NAME}
                env_var = value[2:-1]
                resolved_value = os.getenv(env_var)
                if resolved_value is None:
                    raise ValueError(f"环境变量 {env_var} 未设置")
                resolved_config[key] = resolved_value
            else:
                resolved_config[key] = value
        
        return resolved_config


class TemplateFactory:
    """模板工厂"""
    
    @staticmethod
    def create_knowledge_graph_template(output_path: str):
        """创建通用知识图谱模板配置文件"""
        template_config = {
            "name": "通用知识图谱提取",
            "description": "从文本中提取实体和关系的通用模板",
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
        
        # 保存配置文件
        import yaml
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(template_config, f, allow_unicode=True, indent=2)
        
        return output_path
    
    @staticmethod
    def create_flood_disaster_template(output_path: str):
        """创建洪涝灾害模板配置文件（从原有模板转换）"""
        # 这里可以将原有的洪涝灾害模板转换为配置文件格式
        # 目前返回一个基本的配置
        template_config = {
            "name": "洪涝灾害知识图谱提取",
            "description": "专门用于洪涝灾害相关信息的提取",
            "version": "2.0",
            # ... 这里可以添加完整的洪涝灾害配置
        }
        
        import yaml
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(template_config, f, allow_unicode=True, indent=2)
        
        return output_path