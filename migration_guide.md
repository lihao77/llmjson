# LLMJson 通用化迁移指南

## 概述

本指南展示如何将现有的洪涝灾害专用系统迁移到通用的信息抽取框架，同时保持向后兼容性。

## 迁移策略

### 阶段1：保持兼容的重构

#### 1.1 现有模板转换

将现有的硬编码模板转换为配置文件格式：

```yaml
# templates/flood_disaster.yaml
name: "洪涝灾害知识图谱提取"
description: "专门用于洪涝灾害相关信息的提取"
version: "2.0"

# 输出数据结构定义
output_schema:
  type: "object"
  properties:
    基础实体:
      type: "array"
      items:
        type: "object"
        properties:
          类型: {type: "string", enum: ["事件", "地点", "设施"]}
          名称: {type: "string"}
          唯一ID: {type: "string"}
          地理描述: {type: "string"}
        required: ["类型", "名称", "唯一ID"]
    状态实体:
      type: "array"
      items:
        type: "object"
        properties:
          类型: {type: "string", enum: ["独立状态", "联合状态"]}
          关联实体ID列表: {type: "array", items: {type: "string"}}
          状态ID: {type: "string"}
          时间: {type: "string", pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}至[0-9]{4}-[0-9]{2}-[0-9]{2}$"}
          状态描述: {type: "object"}
        required: ["类型", "关联实体ID列表", "状态ID", "时间", "状态描述"]
    状态关系:
      type: "array"
      items:
        type: "object"
        properties:
          主体状态ID: {type: "string"}
          关系: {type: "string", enum: ["触发", "影响", "调控", "导致"]}
          客体状态ID: {type: "string"}
          依据: {type: "string"}
        required: ["主体状态ID", "关系", "客体状态ID", "依据"]
  required: ["基础实体", "状态实体", "状态关系"]

# 实体类型定义
entity_types:
  - name: "事件"
    description: "直接导致或由洪涝灾害引发的自然或衍生事件"
    id_pattern: "E-<行政区划码>-<日期YYYYMMDD>-<事件类型>"
    examples: ["2023年长江流域暴雨", "某河段决堤事件"]
  - name: "地点"
    description: "自然地理实体（河流、湖泊等）或行政区域（省、市、区、乡镇）"
    id_pattern: "L-<行政区划码>[>子区域] 或 L-<实体类型>-<名称>[>区段]"
    examples: ["长江", "鄱阳湖", "湖北省武汉市"]
  - name: "设施"
    description: "参与防洪、水资源管理或救灾的、具有具体明确名称的人工建造结构"
    id_pattern: "F-<行政区划码>-<设施名称>"
    examples: ["三峡大坝", "龙潭水库排水泵站", "湘江水文站"]

# 关系类型定义
relation_types:
  - name: "触发"
    description: "一个状态触发另一个状态的发生"
  - name: "影响"
    description: "一个状态对另一个状态产生影响"
  - name: "调控"
    description: "通过人为操作调控某种状态"
  - name: "导致"
    description: "直接的因果关系"

# 提示模板（保持原有的详细提示）
system_prompt: |
  你是一个专业的信息抽取系统，专为洪涝灾害领域设计。你的核心任务是精确、无遗漏地从给定文本中抽取出符合下列严格定义的实体、状态和关系。

  ## 实体定义
  
  {entity_types_description}

  ## 状态定义
  
  - 独立状态：描述单一基础实体在特定时空下的状况
  - 联合状态：描述多个基础实体不可分割的共享状态

  ## 关系定义
  
  {relation_types_description}

  ## 输出格式
  
  请严格按照以下JSON格式输出：
  {output_format_example}

  ## 核心原则
  
  1. 忠于原文：仅能提取文本中明确陈述或可直接推断的信息
  2. 确定性优先：如果对某项信息存在模糊性，必须放弃提取
  3. 完整性扫描：确保所有符合定义的实体、状态及关系都被提取

user_prompt: |
  请严格遵循以上所有原则、定义、流程和格式，处理以下文本。返回唯一的、格式正确的JSON输出，不要包含任何解释性文字。

  来源文档: 《{doc_name}》
  待处理文本: {chunk}

# 配置参数
config:
  max_entities_per_chunk: 100
  max_states_per_chunk: 200
  max_relations_per_chunk: 150
  require_evidence: true
  strict_id_format: true
```

#### 1.2 兼容性适配器

创建适配器类，保持现有API不变：

```python
# llmjson/adapters/legacy.py
from typing import Dict, Any, List, Optional, Tuple
from ..templates.base import ConfigurableTemplate
from ..validators.universal import UniversalValidator
from ..processors.universal import UniversalProcessor

class LegacyPromptTemplate:
    """保持与原有PromptTemplate兼容的适配器"""
    
    def __init__(self, template_file: Optional[str] = None):
        if template_file:
            self._template = ConfigurableTemplate(template_file)
        else:
            # 使用默认的洪涝灾害模板
            self._template = ConfigurableTemplate("templates/flood_disaster.yaml")
    
    def create_prompt(self, **kwargs) -> List[Dict[str, str]]:
        """保持原有接口"""
        return self._template.create_prompt(**kwargs)
    
    def get_template(self, template_name: str = None):
        """保持原有接口"""
        return self._template
    
    # 保持其他原有方法...

class LegacyDataValidator:
    """保持与原有DataValidator兼容的适配器"""
    
    def __init__(self):
        # 加载洪涝灾害专用的验证规则
        from ..validators.rules.flood_disaster import FloodDisasterValidationRules
        
        schema = self._load_flood_disaster_schema()
        rules = FloodDisasterValidationRules.get_all_rules()
        
        self._validator = UniversalValidator(schema, rules)
        self.validation_report = {}
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """保持原有接口"""
        validated_data, report = self._validator.validate_data(data)
        
        # 转换报告格式以保持兼容性
        self.validation_report = self._convert_report_format(report)
        
        return validated_data, self.validation_report
    
    def _load_flood_disaster_schema(self):
        """加载洪涝灾害的JSON Schema"""
        template = ConfigurableTemplate("templates/flood_disaster.yaml")
        return template.schema
    
    def _convert_report_format(self, new_report: Dict[str, Any]) -> Dict[str, Any]:
        """将新格式的报告转换为原有格式"""
        return {
            "errors_deleted": new_report.get("errors", []),
            "warnings_modified": [],
            "warnings_unmodified": new_report.get("warnings", []),
            "corrections": new_report.get("corrections", []),
            "error_stats": {"base_entities": set(), "state_entities": set(), "state_relations": set()},
            "error_counts": {"total": len(new_report.get("errors", []))},
            "error_rates": {"total": 0.0}
        }

class LegacyLLMProcessor:
    """保持与原有LLMProcessor兼容的适配器"""
    
    def __init__(self, 
                 api_key: str,
                 base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-4o-mini",
                 prompt_template: Optional[LegacyPromptTemplate] = None,
                 **kwargs):
        
        # 创建通用处理器
        template = prompt_template._template if prompt_template else ConfigurableTemplate("templates/flood_disaster.yaml")
        
        # 创建验证器
        validator_adapter = LegacyDataValidator()
        validator = validator_adapter._validator
        
        self._processor = UniversalProcessor(
            template=template,
            validator=validator,
            api_key=api_key,
            base_url=base_url,
            model=model,
            **kwargs
        )
        
        # 保持原有属性
        self.stats = {"total_requests": 0, "successful_requests": 0, "failed_requests": 0}
    
    def process_chunk(self, chunk: str, doc_name: str = "未知文档") -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """保持原有接口"""
        result, info = self._processor.process_chunk(chunk, doc_name)
        
        # 更新统计信息
        self.stats["total_requests"] += 1
        if info["success"]:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        return result, info
    
    def batch_process(self, chunk_items: List[Tuple[str, int, str]], **kwargs):
        """保持原有接口"""
        # 转换为新格式并调用
        results = []
        for doc_name, chunk_index, chunk in chunk_items:
            result, info = self.process_chunk(chunk, doc_name)
            info.update({"doc_name": doc_name, "chunk_index": chunk_index})
            results.append((result, info))
        return results
```

#### 1.3 向后兼容的初始化

修改主要的`__init__.py`文件：

```python
# llmjson/__init__.py

# 原有的导入保持不变
from .processor import LLMProcessor as _OriginalLLMProcessor
from .prompt_template import PromptTemplate as _OriginalPromptTemplate
from .validator import DataValidator as _OriginalDataValidator

# 新的通用系统
from .processors.universal import UniversalProcessor
from .templates.base import ConfigurableTemplate
from .validators.universal import UniversalValidator
from .factory import ProcessorFactory

# 兼容性适配器
from .adapters.legacy import (
    LegacyLLMProcessor,
    LegacyPromptTemplate, 
    LegacyDataValidator
)

# 为了向后兼容，保持原有的类名
LLMProcessor = LegacyLLMProcessor
PromptTemplate = LegacyPromptTemplate
DataValidator = LegacyDataValidator

# 同时提供新的接口
__all__ = [
    # 兼容接口
    'LLMProcessor',
    'PromptTemplate', 
    'DataValidator',
    
    # 新的通用接口
    'UniversalProcessor',
    'ConfigurableTemplate',
    'UniversalValidator',
    'ProcessorFactory',
    
    # 其他工具
    'WordChunker',
    'ConfigManager',
    'Timer'
]

# 版本信息
__version__ = "2.0.0"
```

### 阶段2：扩展新功能

#### 2.1 创建新的领域模板

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
          severity: {type: "string", enum: ["轻度", "中度", "重度"]}
          onset_date: {type: "string"}
    symptoms:
      type: "array"
      items:
        type: "object"
        properties:
          name: {type: "string"}
          duration: {type: "string"}
          severity: {type: "string"}
          body_part: {type: "string"}
    medications:
      type: "array"
      items:
        type: "object"
        properties:
          name: {type: "string"}
          dosage: {type: "string"}
          frequency: {type: "string"}
          route: {type: "string"}

entity_types:
  - name: "疾病"
    description: "诊断的疾病或病症"
    properties: ["icd_code", "severity", "onset_date"]
  - name: "症状"
    description: "患者表现的症状"
    properties: ["duration", "severity", "body_part"]
  - name: "药物"
    description: "处方或推荐的药物"
    properties: ["dosage", "frequency", "route"]

system_prompt: |
  你是一个医疗信息提取专家。请从医疗文档中提取疾病、症状和药物信息。
  
  提取规则：
  1. 疾病：包括诊断的疾病名称和相关信息
  2. 症状：患者表现的症状及其特征
  3. 药物：处方药物及其用法用量
  
  输出格式：{output_format_example}

user_prompt: |
  请从以下医疗文档中提取相关信息：
  
  文档：{doc_name}
  内容：{chunk}
```

#### 2.2 使用新系统

```python
# 使用新的通用系统
from llmjson import ProcessorFactory

# 医疗实体提取
medical_config = {
    "template": {"config_path": "templates/medical_entities.yaml"},
    "validator": {
        "rules": [
            {"type": "entity_deduplication", "params": {"similarity_threshold": 0.9}},
            {"type": "medical_code_validation", "params": {}}
        ]
    },
    "processor": {
        "api_key": "your-api-key",
        "model": "gpt-4o-mini",
        "temperature": 0.1
    }
}

processor = ProcessorFactory.create_from_config(medical_config)
result, info = processor.process_chunk("患者主诉头痛...", "medical_record.txt")

# 仍然可以使用原有的洪涝灾害系统
from llmjson import LLMProcessor, PromptTemplate

template = PromptTemplate()  # 默认使用洪涝灾害模板
processor = LLMProcessor(api_key="your-api-key", prompt_template=template)
result, info = processor.process_chunk("2023年长江流域发生暴雨...", "flood_report.txt")
```

### 阶段3：完全迁移

#### 3.1 弃用警告

```python
# llmjson/__init__.py
import warnings

def _deprecated_warning(old_name: str, new_name: str):
    warnings.warn(
        f"{old_name} is deprecated and will be removed in version 3.0. "
        f"Please use {new_name} instead.",
        DeprecationWarning,
        stacklevel=3
    )

class LLMProcessor(LegacyLLMProcessor):
    def __init__(self, *args, **kwargs):
        _deprecated_warning("LLMProcessor", "UniversalProcessor with ProcessorFactory")
        super().__init__(*args, **kwargs)

class PromptTemplate(LegacyPromptTemplate):
    def __init__(self, *args, **kwargs):
        _deprecated_warning("PromptTemplate", "ConfigurableTemplate")
        super().__init__(*args, **kwargs)
```

#### 3.2 迁移工具

```python
# tools/migrate_config.py
import json
import yaml
from pathlib import Path

def migrate_legacy_config(old_config_path: str, output_dir: str):
    """将旧的配置迁移到新格式"""
    
    with open(old_config_path, 'r') as f:
        old_config = json.load(f)
    
    # 创建新的配置结构
    new_config = {
        "template": {
            "config_path": "templates/flood_disaster.yaml"
        },
        "validator": {
            "rules": [
                {"type": "flood_disaster_validation", "params": {}}
            ]
        },
        "processor": old_config.get("llm", {})
    }
    
    # 保存新配置
    output_path = Path(output_dir) / "migrated_config.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, ensure_ascii=False, indent=2)
    
    print(f"配置已迁移到: {output_path}")
    print("请使用 ProcessorFactory.create_processor() 加载新配置")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("用法: python migrate_config.py <old_config.json> <output_dir>")
        sys.exit(1)
    
    migrate_legacy_config(sys.argv[1], sys.argv[2])
```

## 迁移时间表

### 第1-2个月：基础重构
- [ ] 实现通用模板系统
- [ ] 创建兼容性适配器
- [ ] 转换现有洪涝灾害模板
- [ ] 确保所有现有测试通过

### 第3-4个月：功能扩展
- [ ] 实现通用验证器
- [ ] 创建更多领域模板
- [ ] 添加插件系统
- [ ] 完善文档和示例

### 第5-6个月：生态建设
- [ ] 创建模板市场
- [ ] 提供可视化配置工具
- [ ] 性能优化和监控
- [ ] 社区反馈和改进

### 第7个月以后：完全迁移
- [ ] 发布3.0版本
- [ ] 移除旧接口
- [ ] 专注于新功能开发

## 风险控制

1. **向后兼容性测试**：确保所有现有代码在新系统下正常工作
2. **性能回归测试**：确保新系统性能不低于原系统
3. **渐进式发布**：通过feature flag控制新功能的启用
4. **完整的迁移文档**：提供详细的迁移指南和示例
5. **社区支持**：建立用户反馈渠道，及时解决迁移问题

这样的迁移策略既保证了现有用户的使用不受影响，又为系统的通用化和扩展奠定了基础。