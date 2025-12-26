"""
通用模板基类

提供模板系统的抽象接口和可配置实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import json
import yaml
import jsonschema
from pathlib import Path


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
    
    def __init__(self, template_config_path: Optional[str] = None):
        if template_config_path is None:
            # 使用默认的通用模板配置
            self.template_config = self._get_default_config()
            self.template_config_path = None
        else:
            self.template_config_path = Path(template_config_path)
            
            with open(template_config_path, 'r', encoding='utf-8') as f:
                if template_config_path.endswith(('.yaml', '.yml')):
                    self.template_config = yaml.safe_load(f)
                else:
                    self.template_config = json.load(f)
        
        super().__init__(self.template_config.get('config', {}))
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认的通用模板配置"""
        return {
            "name": "默认通用信息提取模板",
            "description": "基本的实体和关系提取模板",
            "version": "2.0",
            
            "output_schema": {
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "name": {"type": "string"},
                                "id": {"type": "string"}
                            },
                            "required": ["type", "name", "id"]
                        }
                    },
                    "relations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "relation": {"type": "string"},
                                "target": {"type": "string"}
                            },
                            "required": ["source", "relation", "target"]
                        }
                    }
                },
                "required": ["entities", "relations"]
            },
            
            "output_example": {
                "entities": [
                    {"type": "person", "name": "张三", "id": "P-张三-001"}
                ],
                "relations": [
                    {"source": "P-张三-001", "relation": "工作于", "target": "O-公司-001"}
                ]
            },
            
            "entity_types": [
                {"name": "person", "description": "人物实体"},
                {"name": "organization", "description": "组织机构"},
                {"name": "location", "description": "地理位置"}
            ],
            
            "relation_types": [
                {"name": "工作于", "description": "工作关系"},
                {"name": "位于", "description": "位置关系"}
            ],
            
            "system_prompt": """你是一个专业的信息提取引擎。请从给定文本中准确提取实体和关系信息。

## 实体类型定义
{entity_types}

## 关系类型定义
{relation_types}

## 输出格式要求
请严格按照以下JSON格式输出：
{output_format_example}

## 提取原则
1. 只提取文本中明确提到的信息
2. 确保实体ID的唯一性和一致性
3. 关系必须基于文本中的明确表述
4. 保持输出格式的严格一致性""",
            
            "user_prompt": """请从以下文本中提取实体和关系信息：

文档：{doc_name}
内容：{chunk}"""
        }
    
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
        
        # 1. 自动映射配置项到变量
        for key, value in self.template_config.items():
            # 跳过特殊配置项
            if key in ['template_variables', 'config']: 
                continue
            
            # 如果变量已存在（通过kwargs传入），则跳过
            if key in variables:
                continue

            # 根据类型处理值
            if isinstance(value, (str, int, float, bool)):
                variables[key] = str(value)
            
            elif key in ['output_schema', 'output_example']:
                # Schema和Example强制转为JSON字符串
                variables[key] = json.dumps(value, ensure_ascii=False, indent=2)
            
            elif isinstance(value, list):
                # 列表通常是类型定义，使用列表描述生成器
                variables[key] = self._generate_types_description(value)
            
            elif isinstance(value, dict):
                # 其他字典转为JSON
                variables[key] = json.dumps(value, ensure_ascii=False, indent=2)

        # 2. 如果没有提供output_example但有schema，尝试自动生成
        if 'output_example' not in variables and 'output_schema' in self.template_config:
            variables['output_example'] = self._generate_format_example()

        # 3. 处理自定义变量 (template_variables)
        if 'template_variables' in self.template_config:
            custom_vars = self.template_config['template_variables']
            for var_name, var_config in custom_vars.items():
                if var_name not in variables:
                    variables[var_name] = self._generate_custom_variable(var_config, variables)
        
        return variables
    
    def _generate_types_description(self, types_list: List[Dict[str, Any]]) -> str:
        """通用的类型描述生成器"""
        descriptions = []
        for type_info in types_list:
            if isinstance(type_info, dict):
                name = type_info.get('name', '未知')
                desc = type_info.get('description', '')
                
                # 基本描述
                line = f"- {name}: {desc}"
                
                # 添加额外属性
                extras = []
                for key, value in type_info.items():
                    if key not in ['name', 'description'] and isinstance(value, (str, list)):
                        if isinstance(value, list):
                            extras.append(f"{key}: {', '.join(map(str, value))}")
                        else:
                            extras.append(f"{key}: {value}")
                
                if extras:
                    line += f" ({'; '.join(extras)})"
                
                descriptions.append(line)
            else:
                descriptions.append(f"- {type_info}")
        
        return '\n'.join(descriptions)
    
    def _generate_custom_variable(self, var_config: Dict[str, Any], existing_vars: Dict[str, str]) -> str:
        """生成自定义变量"""
        var_type = var_config.get('type', 'text')
        
        if var_type == 'list_description':
            # 从配置中的某个列表生成描述
            source_key = var_config.get('source')
            if source_key and source_key in self.template_config:
                return self._generate_types_description(self.template_config[source_key])
        
        elif var_type == 'json_format':
            # 生成JSON格式
            source_key = var_config.get('source')
            if source_key and source_key in self.template_config:
                return json.dumps(
                    self.template_config[source_key], 
                    ensure_ascii=False, 
                    indent=var_config.get('indent', 2)
                )
        
        elif var_type == 'template':
            # 使用模板字符串，可以引用已有变量
            template_str = var_config.get('template', '')
            # 合并配置变量和已有变量
            template_vars = {**existing_vars, **var_config.get('variables', {})}
            try:
                return template_str.format(**template_vars)
            except KeyError as e:
                # 如果缺少变量，返回默认值或错误信息
                return var_config.get('default', f'[缺少变量: {e}]')
        
        return var_config.get('default', '')
    
    def _generate_format_example(self) -> str:
        """根据schema和用户定义的示例生成输出格式示例"""
        schema = self.template_config['output_schema']
        
        # 1. 优先使用用户定义的完整示例
        if 'output_example' in self.template_config:
            user_example = self.template_config['output_example']
            return json.dumps(user_example, ensure_ascii=False, indent=2)
        
        # 2. 使用用户定义的字段示例值
        field_examples = self.template_config.get('field_examples', {})
        
        def generate_example_value(prop_schema, prop_name="", path=[]):
            """递归生成示例值"""
            current_path = ".".join(path + [prop_name]) if path else prop_name
            
            # 优先使用用户定义的示例
            if current_path in field_examples:
                return field_examples[current_path]
            if prop_name in field_examples:
                return field_examples[prop_name]
            
            prop_type = prop_schema.get('type')
            
            if prop_type == 'string':
                # 检查是否有枚举值
                if 'enum' in prop_schema:
                    return prop_schema['enum'][0]
                # 使用默认值或占位符
                return prop_schema.get('default', f"<{prop_name}>")
            
            elif prop_type == 'array':
                items_schema = prop_schema.get('items', {})
                example_item = generate_example_value(items_schema, f"{prop_name}_item", path + [prop_name])
                return [example_item] if example_item is not None else []
            
            elif prop_type == 'object':
                example_obj = {}
                for sub_prop_name, sub_prop_schema in prop_schema.get('properties', {}).items():
                    example_obj[sub_prop_name] = generate_example_value(
                        sub_prop_schema, sub_prop_name, path + [prop_name]
                    )
                return example_obj
            
            elif prop_type in ['number', 'integer']:
                return prop_schema.get('default', 0)
            
            elif prop_type == 'boolean':
                return prop_schema.get('default', True)
            
            return None
        
        # 3. 生成基于schema的示例
        if schema.get('type') == 'object':
            example = {}
            for prop_name, prop_schema in schema.get('properties', {}).items():
                example_value = generate_example_value(prop_schema, prop_name)
                if example_value is not None:
                    example[prop_name] = example_value
            
            return json.dumps(example, ensure_ascii=False, indent=2)
        
        return "{}"
    
    def get_template_info(self) -> Dict[str, Any]:
        """获取模板信息"""
        return {
            'name': self.template_config.get('name', 'Unknown'),
            'description': self.template_config.get('description', ''),
            'version': self.template_config.get('version', '1.0'),
            'entity_types': self.template_config.get('entity_types', []),
            'relation_types': self.template_config.get('relation_types', [])
        }