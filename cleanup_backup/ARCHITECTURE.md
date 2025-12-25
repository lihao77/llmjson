# LLMJson 2.0 架构设计说明

## 🎯 设计原则

### 1. **配置驱动**
- 🎛️ 完全基于配置文件的信息提取框架
- 📝 YAML模板定义提取规则和输出格式
- 🔧 JSON配置文件管理处理器参数

### 2. **通用架构**
- 🌐 支持任意领域的信息提取任务
- 🔄 可插拔的模板和验证系统
- 📈 从简单实体提取到复杂知识图谱构建

### 3. **模块化设计**
- 🧩 清晰的组件分离
- 🔌 插件化验证规则
- 🏭 工厂模式创建处理器

## 🏗️ 架构层次

```
llmjson/
├── 📁 核心处理器
│   └── processors/
│       └── universal.py      # 🎯 通用处理器
│
├── 📁 模板系统
│   └── templates/
│       └── base.py          # 📝 可配置模板基类
│
├── 📁 验证系统
│   └── validators/
│       ├── universal.py     # ✅ 通用验证器
│       ├── base.py         # 🏗️ 验证器基类
│       └── rules/          # 📋 验证规则库
│           └── common.py   # 🔧 通用验证规则
│
├── 📁 工厂模式
│   └── factory.py          # 🏭 处理器和模板工厂
│
├── 📁 配置管理
│   └── config.py           # ⚙️ 配置管理器
│
├── 📁 运行模式
│   ├── run_mode.py         # 🚀 文档处理器
│   └── cli.py              # 💻 命令行接口
│
└── 📁 工具模块
    ├── utils.py            # 🛠️ 工具函数
    ├── word_chunker.py     # 📄 文档分块器
    ├── log.py              # 📊 日志系统
    └── exceptions.py       # ⚠️ 异常定义
```

## 🚀 使用方式

### 方式1：配置驱动（推荐）

```python
from llmjson import ProcessorFactory

# 使用配置文件创建处理器
processor = ProcessorFactory.create_processor('configs/universal_template.json')
result, info = processor.process_chunk(text, 'doc.txt')

# ✅ 完全配置驱动
# ✅ 支持任意领域
# ✅ 易于定制和扩展
```

### 方式2：手动创建

```python
from llmjson import UniversalProcessor, ConfigurableTemplate

# 手动创建模板和处理器
template = ConfigurableTemplate('templates/universal.yaml')
processor = UniversalProcessor(
    template=template,
    api_key="your-key",
    model="gpt-4o-mini"
)
result, info = processor.process_chunk(text, 'doc.txt')

# ✅ 灵活控制
# ✅ 程序化配置
# ✅ 动态调整参数
```

### 方式3：快捷创建

```python
from llmjson import ProcessorFactory

# 使用快捷方法创建通用处理器
processor = ProcessorFactory.create_universal_processor(
    api_key="your-key",
    model="gpt-4o-mini"
)
result, info = processor.process_chunk(text, 'doc.txt')

# ✅ 快速开始
# ✅ 使用默认配置
# ✅ 适合简单场景
```

## 🔍 核心组件详解

### 1. UniversalProcessor（通用处理器）

```python
class UniversalProcessor:
    """通用处理器，支持任意领域的信息抽取"""
    
    def __init__(self, template, validator=None, **llm_config):
        self.template = template      # 模板实例
        self.validator = validator    # 验证器实例（可选）
        # LLM配置...
    
    def process_chunk(self, chunk, doc_name):
        # 1. 使用模板创建提示
        # 2. 调用LLM API
        # 3. 提取和验证JSON
        # 4. 返回结构化数据
```

### 2. ConfigurableTemplate（可配置模板）

```python
class ConfigurableTemplate(BaseTemplate):
    """基于YAML配置文件的模板"""
    
    def __init__(self, config_path=None):
        # 加载YAML配置
        # 解析模板变量
        # 构建提示模板
    
    def create_prompt(self, **kwargs):
        # 替换模板变量
        # 生成完整提示
        # 返回messages格式
```

### 3. UniversalValidator（通用验证器）

```python
class UniversalValidator(BaseValidator):
    """基于JSON Schema的通用验证器"""
    
    def __init__(self, schema, custom_rules=None):
        self.schema = schema           # JSON Schema
        self.custom_rules = custom_rules  # 自定义规则
    
    def validate_data(self, data):
        # 1. JSON Schema验证
        # 2. 自定义规则验证
        # 3. 数据修正
        # 4. 返回验证结果
```

### 4. ProcessorFactory（处理器工厂）

```python
class ProcessorFactory:
    """处理器工厂，根据配置创建处理器"""
    
    @staticmethod
    def create_processor(config_path):
        # 1. 加载配置文件
        # 2. 创建模板实例
        # 3. 创建验证器实例
        # 4. 创建处理器实例
        
    @staticmethod
    def create_universal_processor(**kwargs):
        # 快捷创建通用处理器
```

## 📊 配置文件结构

### 处理器配置 (`configs/*.json`)

```json
{
  "template": {
    "config_path": "templates/universal.yaml"
  },
  "validator": {
    "type": "universal",
    "rules": [
      {"type": "entity_deduplication"},
      {"type": "relation_validation"}
    ]
  },
  "processor": {
    "api_key": "${OPENAI_API_KEY}",
    "base_url": "${OPENAI_BASE_URL}",
    "model": "${OPENAI_MODEL}",
    "temperature": 0.1,
    "max_tokens": 4000
  }
}
```

### 模板配置 (`templates/*.yaml`)

```yaml
name: "通用信息提取模板"
description: "可配置的通用信息提取模板"
version: "2.0"

# 输出数据结构定义
output_schema:
  type: "object"
  properties:
    entities:
      type: "array"
      items:
        type: "object"
        properties:
          type: {type: "string"}
          name: {type: "string"}
          id: {type: "string"}

# 实体类型定义
entity_types:
  - name: "person"
    description: "人物实体"

# 提示模板
system_prompt: |
  请从文本中提取实体信息。
  
  ## 实体类型
  {entity_types}
  
  ## 输出格式
  {output_format_example}

user_prompt: |
  文档：{doc_name}
  内容：{chunk}
```

## 🔧 扩展机制

### 1. 自定义模板

创建新的YAML模板文件，定义：
- 输出数据结构 (`output_schema`)
- 实体/关系类型 (`entity_types`, `relation_types`)
- 提示模板 (`system_prompt`, `user_prompt`)
- 输出示例 (`output_example`)

### 2. 自定义验证规则

```python
from llmjson.validators.base import ValidationRule

class MyCustomRule(ValidationRule):
    def validate(self, data):
        # 实现自定义验证逻辑
        return ValidationResult(...)
```

### 3. 自定义处理器

```python
from llmjson.processors.universal import UniversalProcessor

class MyCustomProcessor(UniversalProcessor):
    def process_chunk(self, chunk, doc_name):
        # 添加自定义处理逻辑
        return super().process_chunk(chunk, doc_name)
```

## 📈 性能特性

### 1. 智能JSON提取
- 多种解析策略
- 自动错误修复
- 格式验证

### 2. 并发处理
- 多线程文档处理
- 流式处理模式
- 内存优化

### 3. 错误处理
- 重试机制
- 详细错误报告
- 优雅降级

## 🎯 使用场景

### 1. 通用信息提取
- 人物、组织、地点提取
- 关系识别
- 属性抽取

### 2. 领域特化提取
- 学术论文信息提取
- 新闻事件提取
- 产品信息提取

### 3. 知识图谱构建
- 实体识别和链接
- 关系抽取
- 图谱构建

## 🔧 开发工具

### 1. 命令行工具

```bash
# 创建配置文件
python -m llmjson.cli create-config --output config.json

# 处理文档
python -m llmjson.cli process --config config.json --input document.txt

# 验证数据
python -m llmjson.cli validate --input data.json
```

### 2. 模板工厂

```python
from llmjson import TemplateFactory

# 创建通用模板
TemplateFactory.create_universal_template("my_template.yaml")
```

## 📚 最佳实践

### 1. 模板设计
- 提供清晰的输出示例
- 定义完整的数据结构
- 使用描述性的实体类型

### 2. 配置管理
- 使用环境变量管理敏感信息
- 为不同环境创建不同配置
- 定期验证配置有效性

### 3. 性能优化
- 合理设置分块大小
- 使用并发处理大量文档
- 监控API使用量

这个v2架构提供了一个**完全配置驱动**、**高度可扩展**的信息提取框架，支持从简单的实体提取到复杂的知识图谱构建等各种任务。