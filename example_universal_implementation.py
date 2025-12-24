#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLMJson 通用化实现示例

展示如何将现有的洪涝灾害专用系统改造为通用的信息抽取框架
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from abc import ABC, abstractmethod
import json
import yaml
import jsonschema
from pathlib import Path

# ============================================================================
# 1. 通用模板系统
# ============================================================================

class BaseTemplate(ABC):
    """模板基类，定义通用接口"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.schema = self.load_schema()
    
    @abstractmethod
    def load_schema(self) -> Dict[str, Any]:
        """加载输出数据的JSON Schema"""
        pass
    
    @abstractmethod
    def create_prompt(self, **kwargs) -> List[Dict[str, str]]:
        """创建提示消息"""
        pass
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出是否符合预期格式"""
        try:
            jsonschema.validate(output, self.schema)
            return True
        except jsonschema.ValidationError:
            return False

class ConfigurableTemplate(BaseTemplate):
    """可配置的通用模板"""
    
    def __init__(self, template_config_path: str):
        self.template_config_path = Path(template_config_path)
        
        with open(template_config_path, 'r', encoding='utf-8') as f:
            if template_config_path.endswith(('.yaml', '.yml')):
                self.template_config = yaml.safe_load(f)
            else:
                self.template_config = json.load(f)
        
        super().__init__(self.template_config.get('config', {}))
    
    def load_schema(self) -> Dict[str, Any]:
        return self.template_config.get('output_schema', {})
    
    def create_prompt(self, **kwargs) -> List[Dict[str, str]]:
        messages = []
        
        # 准备模板变量
        template_vars = self._prepare_template_variables(**kwargs)
        
        # 系统消息
        if 'system_prompt' in self.template_config:
            system_content = self.template_config['system_prompt'].format(**template_vars)
            messages.append({"role": "system", "content": system_content})
        
        # 用户消息
        if 'user_prompt' in self.template_config:
            user_content = self.template_config['user_prompt'].format(**template_vars)
            messages.append({"role": "user", "content": user_content})
        
        return messages
    
    def _prepare_template_variables(self, **kwargs) -> Dict[str, str]:
        """准备模板变量"""
        variables = kwargs.copy()
        
        # 生成实体类型描述
        if 'entity_types' in self.template_config:
            entity_descriptions = []
            for entity_type in self.template_config['entity_types']:
                desc = f"- {entity_type['name']}: {entity_type['description']}"
                if 'properties' in entity_type:
                    desc += f" (属性: {', '.join(entity_type['properties'])})"
                entity_descriptions.append(desc)
            variables['entity_types_description'] = '\n'.join(entity_descriptions)
        
        # 生成关系类型描述
        if 'relation_types' in self.template_config:
            relation_descriptions = []
            for relation_type in self.template_config['relation_types']:
                desc = f"- {relation_type['name']}: {relation_type['description']}"
                relation_descriptions.append(desc)
            variables['relation_types_description'] = '\n'.join(relation_descriptions)
        
        # 生成输出格式示例
        if 'output_schema' in self.template_config:
            variables['output_format_example'] = self._generate_format_example()
        
        return variables
    
    def _generate_format_example(self) -> str:
        """根据schema生成输出格式示例"""
        schema = self.template_config['output_schema']
        
        if schema.get('type') == 'object':
            example = {}
            for prop_name, prop_schema in schema.get('properties', {}).items():
                if prop_schema.get('type') == 'array':
                    example[prop_name] = []
                elif prop_schema.get('type') == 'object':
                    example[prop_name] = {}
                else:
                    example[prop_name] = f"<{prop_name}>"
            
            return json.dumps(example, ensure_ascii=False, indent=2)
        
        return "{}"

# ============================================================================
# 2. 通用验证器系统
# ============================================================================

class ValidationRule:
    """验证规则基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def validate(self, data: Dict[str, Any]) -> 'ValidationResult':
        """执行验证"""
        raise NotImplementedError

class ValidationResult:
    """验证结果"""
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.corrections = []
    
    def add_error(self, message: str):
        self.is_valid = False
        self.errors.append(message)
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def add_correction(self, correction):
        self.corrections.append(correction)

class UniversalValidator:
    """通用数据验证器"""
    
    def __init__(self, schema: Dict[str, Any], custom_rules: Optional[List[ValidationRule]] = None):
        self.schema = schema
        self.custom_rules = custom_rules or []
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """验证数据"""
        validated_data = data.copy()
        validation_report = {
            "errors": [],
            "warnings": [],
            "corrections": [],
            "schema_validation": True,
            "custom_validation": True
        }
        
        # 1. JSON Schema验证
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            validation_report["schema_validation"] = False
            validation_report["errors"].append(f"Schema validation failed: {e.message}")
        
        # 2. 自定义规则验证
        for rule in self.custom_rules:
            try:
                rule_result = rule.validate(validated_data)
                if not rule_result.is_valid:
                    validation_report["custom_validation"] = False
                    validation_report["errors"].extend(rule_result.errors)
                
                validation_report["warnings"].extend(rule_result.warnings)
                validation_report["corrections"].extend([c.description for c in rule_result.corrections])
                
                # 应用修正
                for correction in rule_result.corrections:
                    validated_data = correction.apply(validated_data)
                    
            except Exception as e:
                validation_report["errors"].append(f"Custom rule '{rule.name}' failed: {str(e)}")
        
        return validated_data, validation_report

# ============================================================================
# 3. 示例验证规则
# ============================================================================

class EntityDeduplicationRule(ValidationRule):
    """实体去重规则"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        super().__init__("entity_deduplication", "去除重复的实体")
        self.similarity_threshold = similarity_threshold
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        
        entities = data.get('entities', [])
        if not entities:
            return result
        
        # 简单的名称相似度检查
        seen_names = set()
        duplicates = []
        
        for i, entity in enumerate(entities):
            name = entity.get('name', '').lower().strip()
            if name in seen_names:
                duplicates.append(i)
                result.add_warning(f"发现重复实体: {entity.get('name')}")
            else:
                seen_names.add(name)
        
        # 创建修正操作
        if duplicates:
            correction = EntityRemovalCorrection(duplicates)
            result.add_correction(correction)
        
        return result

class EntityRemovalCorrection:
    """实体移除修正操作"""
    
    def __init__(self, indices_to_remove: List[int]):
        self.indices_to_remove = sorted(indices_to_remove, reverse=True)
        self.description = f"移除重复实体 (索引: {indices_to_remove})"
    
    def apply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """应用修正"""
        corrected_data = data.copy()
        entities = corrected_data.get('entities', [])
        
        for index in self.indices_to_remove:
            if 0 <= index < len(entities):
                entities.pop(index)
        
        corrected_data['entities'] = entities
        return corrected_data

# ============================================================================
# 4. 通用处理器
# ============================================================================

class UniversalProcessor:
    """通用处理器"""
    
    def __init__(self, 
                 template: BaseTemplate,
                 validator: Optional[UniversalValidator] = None,
                 llm_client=None,  # 这里应该是实际的LLM客户端
                 **kwargs):
        self.template = template
        self.validator = validator
        self.llm_client = llm_client
        self.config = kwargs
    
    def process_chunk(self, chunk: str, doc_name: str = "未知文档") -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """处理文本块"""
        
        try:
            # 1. 创建提示
            prompt = self.template.create_prompt(chunk=chunk, doc_name=doc_name)
            
            # 2. 调用LLM (这里需要实际的LLM调用逻辑)
            response = self._call_llm(prompt)
            
            # 3. 解析JSON
            json_data = self._parse_json_response(response)
            
            if json_data is None:
                return None, {"success": False, "error": "JSON解析失败"}
            
            # 4. 模板验证
            if not self.template.validate_output(json_data):
                return None, {"success": False, "error": "输出格式不符合模板要求"}
            
            # 5. 数据验证和修正
            validation_report = {"validation_skipped": True}
            if self.validator:
                json_data, validation_report = self.validator.validate_data(json_data)
            
            return json_data, {
                "success": True,
                "validation": validation_report,
                "doc_name": doc_name
            }
            
        except Exception as e:
            return None, {"success": False, "error": str(e)}
    
    def _call_llm(self, prompt: List[Dict[str, str]]) -> str:
        """调用LLM (示例实现)"""
        # 这里应该是实际的LLM调用逻辑
        # 为了演示，返回一个示例响应
        return '{"entities": [], "relations": []}'
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析JSON响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 这里可以添加更复杂的JSON修复逻辑
            return None

# ============================================================================
# 5. 配置工厂
# ============================================================================

class ProcessorFactory:
    """处理器工厂"""
    
    @staticmethod
    def create_processor(config_path: str) -> UniversalProcessor:
        """根据配置文件创建处理器"""
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 1. 创建模板
        template_config = config.get('template', {})
        if 'config_path' in template_config:
            template = ConfigurableTemplate(template_config['config_path'])
        else:
            raise ValueError("Template configuration missing")
        
        # 2. 创建验证器
        validator = None
        if 'validator' in config:
            validator_config = config['validator']
            custom_rules = []
            
            # 加载验证规则
            for rule_config in validator_config.get('rules', []):
                if rule_config['type'] == 'entity_deduplication':
                    rule = EntityDeduplicationRule(**rule_config.get('params', {}))
                    custom_rules.append(rule)
            
            validator = UniversalValidator(
                schema=template.schema,
                custom_rules=custom_rules
            )
        
        # 3. 创建处理器
        processor_config = config.get('processor', {})
        return UniversalProcessor(
            template=template,
            validator=validator,
            **processor_config
        )

# ============================================================================
# 6. 使用示例
# ============================================================================

def create_knowledge_graph_template():
    """创建通用知识图谱模板配置"""
    
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
                            "properties": {"type": "object"}
                        },
                        "required": ["source", "target", "type"]
                    }
                }
            },
            "required": ["entities", "relations"]
        },
        
        "entity_types": [
            {
                "name": "Person",
                "description": "人物实体",
                "properties": ["age", "occupation", "location"]
            },
            {
                "name": "Organization", 
                "description": "组织机构",
                "properties": ["type", "location", "founded"]
            },
            {
                "name": "Location",
                "description": "地理位置", 
                "properties": ["type", "coordinates"]
            }
        ],
        
        "relation_types": [
            {
                "name": "works_for",
                "description": "工作关系"
            },
            {
                "name": "located_in", 
                "description": "位置关系"
            },
            {
                "name": "founded_by",
                "description": "创立关系"
            }
        ],
        
        "system_prompt": """你是一个专业的信息抽取系统。请从给定的文本中提取实体和关系。

实体类型：
{entity_types_description}

关系类型：
{relation_types_description}

请严格按照以下JSON格式输出：
{output_format_example}

注意：
1. 每个实体必须有唯一的ID
2. 关系的source和target必须是已提取实体的ID
3. 只提取文本中明确提及的信息""",
        
        "user_prompt": """请从以下文本中提取实体和关系：

文档：《{doc_name}》
内容：{chunk}

请返回严格符合格式的JSON数据。"""
    }
    
    return template_config

def create_processor_config():
    """创建处理器配置"""
    
    config = {
        "template": {
            "config_path": "templates/knowledge_graph.yaml"
        },
        "validator": {
            "rules": [
                {
                    "type": "entity_deduplication",
                    "params": {"similarity_threshold": 0.8}
                }
            ]
        },
        "processor": {
            "temperature": 0.1,
            "max_tokens": 4000
        }
    }
    
    return config

def demo_usage():
    """演示使用方法"""
    
    # 1. 创建模板配置文件
    template_config = create_knowledge_graph_template()
    
    # 保存模板配置
    Path("templates").mkdir(exist_ok=True)
    with open("templates/knowledge_graph.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(template_config, f, ensure_ascii=False, indent=2)
    
    # 2. 创建处理器配置
    processor_config = create_processor_config()
    
    with open("processor_config.json", 'w', encoding='utf-8') as f:
        json.dump(processor_config, f, ensure_ascii=False, indent=2)
    
    # 3. 创建处理器
    processor = ProcessorFactory.create_processor("processor_config.json")
    
    # 4. 处理文本
    text = "苹果公司是一家位于加利福尼亚州的科技公司，由史蒂夫·乔布斯创立。"
    result, info = processor.process_chunk(text, "example.txt")
    
    print("处理结果：", result)
    print("处理信息：", info)

if __name__ == "__main__":
    demo_usage()