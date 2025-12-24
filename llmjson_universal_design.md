# LLMJson 通用化设计方案

## 问题分析

当前的llmjson项目专门针对洪涝灾害知识图谱提取，存在以下局限性：

1. **模板固化**: 提示模板硬编码了洪涝灾害相关的实体类型和关系
2. **验证规则特化**: 数据验证器针对特定的ID格式和数据结构
3. **输出结构固定**: JSON输出格式固定为特定的三层结构

## 通用化改进方案

### 1. 模板系统重构 (Template System Refactoring)

#### 1.1 抽象模板基类

```python
# llmjson/templates/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import json
import yaml

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
    
    @abstractmethod
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出是否符合预期格式"""
        pass

class ConfigurableTemplate(BaseTemplate):
    """可配置的通用模板"""
    
    def __init__(self, template_config_path: str):
        with open(template_config_path, 'r', encoding='utf-8') as f:
            if template_config_path.endswith('.yaml') or template_config_path.endswith('.yml'):
                self.template_config = yaml.safe_load(f)
            else:
                self.template_config = json.load(f)
        
        super().__init__(self.template_config.get('config', {}))
    
    def load_schema(self) -> Dict[str, Any]:
        return self.template_config.get('output_schema', {})
    
    def create_prompt(self, **kwargs) -> List[Dict[str, str]]:
        messages = []
        
        # 系统消息
        if 'system_prompt' in self.template_config:
            system_content = self.template_config['system_prompt'].format(**kwargs)
            messages.append({"role": "system", "content": system_content})
        
        # 用户消息
        if 'user_prompt' in self.template_config:
            user_content = self.template_config['user_prompt'].format(**kwargs)
            messages.append({"role": "user", "content": user_content})
        
        return messages
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        # 基于JSON Schema验证
        try:
            import jsonschema
            jsonschema.validate(output, self.schema)
            return True
        except:
            return False
```

#### 1.2 模板配置文件格式

```yaml
# templates/knowledge_graph.yaml
name: "通用知识图谱提取"
description: "从文本中提取实体和关系的通用模板"
version: "1.0"

# 输出数据的JSON Schema
output_schema:
  type: "object"
  properties:
    entities:
      type: "array"
      items:
        type: "object"
        properties:
          id: {type: "string"}
          type: {type: "string"}
          name: {type: "string"}
          properties: {type: "object"}
        required: ["id", "type", "name"]
    relations:
      type: "array"
      items:
        type: "object"
        properties:
          id: {type: "string"}
          source: {type: "string"}
          target: {type: "string"}
          type: {type: "string"}
          properties: {type: "object"}
        required: ["source", "target", "type"]
  required: ["entities", "relations"]

# 实体类型定义
entity_types:
  - name: "Person"
    description: "人物实体"
    properties: ["age", "occupation", "location"]
  - name: "Organization"
    description: "组织机构"
    properties: ["type", "location", "founded"]
  - name: "Location"
    description: "地理位置"
    properties: ["type", "coordinates", "population"]

# 关系类型定义
relation_types:
  - name: "works_for"
    description: "工作关系"
    source_types: ["Person"]
    target_types: ["Organization"]
  - name: "located_in"
    description: "位置关系"
    source_types: ["Person", "Organization"]
    target_types: ["Location"]

# 提示模板
system_prompt: |
  你是一个专业的信息抽取系统。请从给定的文本中提取实体和关系。
  
  实体类型：
  {entity_types_description}
  
  关系类型：
  {relation_types_description}
  
  请严格按照以下JSON格式输出：
  {output_format_example}

user_prompt: |
  请从以下文本中提取实体和关系：
  
  文档：《{doc_name}》
  内容：{chunk}
  
  请返回严格符合格式的JSON数据。

# 配置参数
config:
  max_entities_per_chunk: 50
  max_relations_per_chunk: 100
  require_evidence: true
```

### 2. 通用验证器 (Universal Validator)

```python
# llmjson/validators/universal.py
from typing import Dict, Any, List, Optional
import jsonschema
from ..validators.base import BaseValidator

class UniversalValidator(BaseValidator):
    """通用数据验证器，基于JSON Schema"""
    
    def __init__(self, schema: Dict[str, Any], custom_rules: Optional[List] = None):
        self.schema = schema
        self.custom_rules = custom_rules or []
        super().__init__()
    
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
                    
                    # 应用修正
                    if rule_result.corrections:
                        validated_data = rule_result.apply_corrections(validated_data)
                        validation_report["corrections"].extend(rule_result.corrections)
            except Exception as e:
                validation_report["errors"].append(f"Custom rule validation failed: {str(e)}")
        
        return validated_data, validation_report

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
    
    def apply_corrections(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """应用修正"""
        corrected_data = data.copy()
        for correction in self.corrections:
            corrected_data = correction.apply(corrected_data)
        return corrected_data
```

### 3. 插件化处理器 (Plugin-based Processor)

```python
# llmjson/processors/universal.py
from typing import Dict, Any, Optional, List
from ..templates.base import BaseTemplate
from ..validators.base import BaseValidator
from ..processors.base import BaseProcessor

class UniversalProcessor(BaseProcessor):
    """通用处理器，支持插件化扩展"""
    
    def __init__(self, 
                 template: BaseTemplate,
                 validator: Optional[BaseValidator] = None,
                 plugins: Optional[List['ProcessorPlugin']] = None,
                 **kwargs):
        self.template = template
        self.validator = validator
        self.plugins = plugins or []
        super().__init__(**kwargs)
    
    def process_chunk(self, chunk: str, doc_name: str = "未知文档") -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """处理文本块"""
        
        # 1. 预处理插件
        for plugin in self.plugins:
            if hasattr(plugin, 'preprocess'):
                chunk = plugin.preprocess(chunk, doc_name)
        
        # 2. 创建提示
        prompt = self.template.create_prompt(chunk=chunk, doc_name=doc_name)
        
        # 3. 调用LLM
        reasoning, response = self._call_llm_api(prompt)
        
        # 4. 提取JSON
        json_data = self._extract_json(response)
        
        if json_data is None:
            return None, {"success": False, "error": "JSON解析失败"}
        
        # 5. 模板验证
        if not self.template.validate_output(json_data):
            return None, {"success": False, "error": "输出格式不符合模板要求"}
        
        # 6. 数据验证
        if self.validator:
            json_data, validation_report = self.validator.validate_data(json_data)
        else:
            validation_report = {"validation_skipped": True}
        
        # 7. 后处理插件
        for plugin in self.plugins:
            if hasattr(plugin, 'postprocess'):
                json_data = plugin.postprocess(json_data, doc_name)
        
        return json_data, {
            "success": True,
            "reasoning": reasoning,
            "validation": validation_report
        }

class ProcessorPlugin:
    """处理器插件基类"""
    
    def preprocess(self, chunk: str, doc_name: str) -> str:
        """预处理文本"""
        return chunk
    
    def postprocess(self, data: Dict[str, Any], doc_name: str) -> Dict[str, Any]:
        """后处理数据"""
        return data
```

### 4. 配置驱动的工厂模式

```python
# llmjson/factory.py
from typing import Dict, Any, Optional
from .processors.universal import UniversalProcessor
from .templates.base import ConfigurableTemplate
from .validators.universal import UniversalValidator
import importlib

class ProcessorFactory:
    """处理器工厂，根据配置创建处理器"""
    
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
            template_class = ProcessorFactory._load_class(template_config['class'])
            template = template_class(**template_config.get('params', {}))
        
        # 2. 创建验证器
        validator = None
        if 'validator' in config:
            validator_config = config['validator']
            if validator_config.get('type') == 'universal':
                validator = UniversalValidator(
                    schema=template.schema,
                    custom_rules=ProcessorFactory._load_validation_rules(
                        validator_config.get('rules', [])
                    )
                )
            else:
                validator_class = ProcessorFactory._load_class(validator_config['class'])
                validator = validator_class(**validator_config.get('params', {}))
        
        # 3. 加载插件
        plugins = []
        for plugin_config in config.get('plugins', []):
            plugin_class = ProcessorFactory._load_class(plugin_config['class'])
            plugin = plugin_class(**plugin_config.get('params', {}))
            plugins.append(plugin)
        
        # 4. 创建处理器
        processor_config = config.get('processor', {})
        return UniversalProcessor(
            template=template,
            validator=validator,
            plugins=plugins,
            **processor_config
        )
    
    @staticmethod
    def _load_class(class_path: str):
        """动态加载类"""
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    
    @staticmethod
    def _load_validation_rules(rules_config: List[Dict[str, Any]]):
        """加载验证规则"""
        rules = []
        for rule_config in rules_config:
            rule_class = ProcessorFactory._load_class(rule_config['class'])
            rule = rule_class(**rule_config.get('params', {}))
            rules.append(rule)
        return rules
```

### 5. 使用示例

#### 5.1 通用知识图谱提取配置

```json
{
  "template": {
    "config_path": "templates/knowledge_graph.yaml"
  },
  "validator": {
    "type": "universal",
    "rules": [
      {
        "class": "llmjson.validators.rules.EntityDeduplicationRule",
        "params": {"similarity_threshold": 0.8}
      },
      {
        "class": "llmjson.validators.rules.RelationConsistencyRule",
        "params": {}
      }
    ]
  },
  "plugins": [
    {
      "class": "llmjson.plugins.TextCleanupPlugin",
      "params": {"remove_urls": true, "normalize_whitespace": true}
    }
  ],
  "processor": {
    "api_key": "${OPENAI_API_KEY}",
    "model": "gpt-4o-mini",
    "temperature": 0.1,
    "max_tokens": 4000
  }
}
```

#### 5.2 医疗实体提取配置

```yaml
# templates/medical_entities.yaml
name: "医疗实体提取"
description: "从医疗文本中提取疾病、症状、药物等实体"

output_schema:
  type: "object"
  properties:
    diseases:
      type: "array"
      items:
        type: "object"
        properties:
          name: {type: "string"}
          icd_code: {type: "string"}
          severity: {type: "string"}
    symptoms:
      type: "array"
      items:
        type: "object"
        properties:
          name: {type: "string"}
          duration: {type: "string"}
          severity: {type: "string"}
    medications:
      type: "array"
      items:
        type: "object"
        properties:
          name: {type: "string"}
          dosage: {type: "string"}
          frequency: {type: "string"}

system_prompt: |
  你是一个医疗信息提取专家。请从医疗文档中提取疾病、症状和药物信息。
  
  提取规则：
  1. 疾病：包括诊断的疾病名称和ICD编码（如果有）
  2. 症状：患者表现的症状及其严重程度
  3. 药物：处方药物及其用法用量
  
  输出格式：
  {
    "diseases": [...],
    "symptoms": [...], 
    "medications": [...]
  }

user_prompt: |
  请从以下医疗文档中提取相关信息：
  
  {chunk}
```

#### 5.3 简单使用

```python
from llmjson import ProcessorFactory

# 使用通用知识图谱配置
processor = ProcessorFactory.create_processor("configs/knowledge_graph.json")

# 处理文本
text = "苹果公司是一家位于加利福尼亚州的科技公司，由史蒂夫·乔布斯创立。"
result, info = processor.process_chunk(text, "example.txt")

if info['success']:
    print("提取的实体：", result['entities'])
    print("提取的关系：", result['relations'])

# 使用医疗实体提取配置
medical_processor = ProcessorFactory.create_processor("configs/medical.json")
medical_text = "患者主诉头痛，诊断为偏头痛，开具布洛芬200mg，每日三次。"
result, info = medical_processor.process_chunk(medical_text, "medical_record.txt")
```

## 实施建议

### 阶段1：向后兼容的重构
1. 保持现有API不变
2. 将现有的洪涝灾害模板转换为新的配置格式
3. 添加通用模板和验证器作为可选功能

### 阶段2：扩展功能
1. 实现更多领域的模板（医疗、法律、金融等）
2. 开发常用的验证规则和插件
3. 提供模板和配置的可视化编辑器

### 阶段3：生态建设
1. 建立模板市场，用户可以分享和下载模板
2. 提供模板性能评估和优化建议
3. 支持多模态输入（图片、表格等）

这样的设计既保持了现有功能的完整性，又为未来的扩展提供了灵活的架构。