# LLMJson 2.0 - 通用化信息抽取框架

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)](#)

## 🎉 版本2.0新特性

LLMJson 2.0 是一个重大升级，将原本专用于洪涝灾害的信息抽取系统改造为**通用化的信息抽取框架**，同时保持完全的向后兼容性。

### ✨ 主要改进

- 🌍 **通用化支持**: 支持任意领域的信息抽取（医疗、法律、金融、新闻等）
- 🔧 **配置驱动**: 通过YAML/JSON配置文件定义抽取模板，无需修改代码
- 🧩 **插件化验证**: 可插拔的验证规则系统
- 🔄 **完全兼容**: 原有代码无需任何修改即可使用
- 🏭 **工厂模式**: 通过配置文件快速创建不同领域的处理器
- 📊 **JSON Schema**: 基于标准的输出格式验证

### 🆚 版本对比

| 特性 | v1.0 (洪涝灾害专用) | v2.0 (通用框架) |
|------|-------------------|----------------|
| 支持领域 | 仅洪涝灾害 | 任意领域 |
| 模板定义 | 硬编码 | 配置文件 |
| 输出格式 | 固定结构 | 灵活的JSON Schema |
| 扩展方式 | 修改源码 | 添加配置文件 |
| 验证规则 | 特定逻辑 | 插件化规则 |
| 向后兼容 | - | ✅ 完全兼容 |

## 🚀 快速开始

### 🌊 洪涝灾害文档处理示例

#### 一键启动（推荐）
```bash
# 克隆或下载项目后
python quick_start.py
```

#### 分步执行
```bash
# 1. 配置API密钥
python setup_environment.py

# 2. 运行洪涝灾害处理示例
python flood_disaster_example.py
```

#### 配置API密钥
支持多种API服务：

```bash
# OpenAI官方
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# DeepSeek
OPENAI_API_KEY=your-deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

# 本地Ollama
OPENAI_API_KEY=not-needed
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:8b
```

### 方式1：使用新的通用系统（推荐）

```python
from llmjson import ProcessorFactory

# 从配置文件创建处理器
processor = ProcessorFactory.create_processor('configs/flood_disaster_complete.json')

# 处理文本
text = "2023年长江流域发生暴雨，导致多地受灾..."
result, info = processor.process_chunk(text, 'flood_report.txt')

if info['success']:
    print("基础实体：", len(result['基础实体']))
    print("状态实体：", len(result['状态实体']))
    print("状态关系：", len(result['状态关系']))
```

### 方式2：原有代码无需修改

```python
# 原有代码继续正常工作，自动使用兼容适配器
from llmjson import LLMProcessor

processor = LLMProcessor(
    api_key="your-openai-api-key",
    model="gpt-4o-mini"
)

# 处理洪涝灾害文本（保持原有功能）
text = "2023年长江流域发生暴雨，导致多地受灾..."
result, info = processor.process_chunk(text, 'flood_report.txt')

if info['success']:
    print("基础实体：", result['基础实体'])
    print("状态实体：", result['状态实体'])
    print("状态关系：", result['状态关系'])
```

### 方式3：快速创建专用处理器

```python
from llmjson import ProcessorFactory

# 创建洪涝灾害专用处理器
flood_processor = ProcessorFactory.create_flood_disaster_processor(
    api_key="your-api-key"
)

# 创建通用知识图谱处理器
kg_processor = ProcessorFactory.create_processor('configs/knowledge_graph.json')
```

## 📋 支持的领域示例

### 1. 通用知识图谱

```yaml
# templates/knowledge_graph.yaml
name: "通用知识图谱提取"
output_schema:
  type: "object"
  properties:
    entities:
      type: "array"
      items:
        properties:
          id: {type: "string"}
          type: {type: "string"}
          name: {type: "string"}
    relations:
      type: "array"
      items:
        properties:
          source: {type: "string"}
          target: {type: "string"}
          type: {type: "string"}

entity_types:
  - {name: "Person", description: "人物实体"}
  - {name: "Organization", description: "组织机构"}
  - {name: "Location", description: "地理位置"}

relation_types:
  - {name: "works_for", description: "工作关系"}
  - {name: "located_in", description: "位置关系"}
```

### 2. 医疗实体提取

```yaml
# templates/medical_entities.yaml
name: "医疗实体提取"
output_schema:
  type: "object"
  properties:
    diseases: {type: "array"}
    symptoms: {type: "array"}
    medications: {type: "array"}

system_prompt: |
  你是一个医疗信息提取专家。请从医疗文档中提取疾病、症状和药物信息。
```

### 3. 新闻事件分析

```yaml
# templates/news_events.yaml
name: "新闻事件提取"
output_schema:
  type: "object"
  properties:
    events:
      type: "array"
      items:
        properties:
          title: {type: "string"}
          type: {type: "string"}
          participants: {type: "array"}
          location: {type: "string"}
          time: {type: "string"}
```

## 🔧 配置系统

### 处理器配置文件

```json
{
  "template": {
    "config_path": "templates/knowledge_graph.yaml"
  },
  "validator": {
    "type": "universal",
    "rules": [
      {
        "type": "entity_deduplication",
        "params": {"similarity_threshold": 0.8}
      },
      {
        "type": "relation_validation",
        "params": {"check_entity_existence": true}
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
```

### 环境变量支持

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-4o-mini"
export LLM_TEMPERATURE="0.1"
```

## 🧩 插件化验证

### 内置验证规则

- **实体去重**: 自动识别和移除重复实体
- **关系验证**: 检查关系的源和目标实体是否存在
- **时间格式**: 验证和标准化时间格式
- **洪涝灾害专用**: 保持原有的专业验证逻辑

### 自定义验证规则

```python
from llmjson.validators.base import ValidationRule, ValidationResult

class CustomValidationRule(ValidationRule):
    def __init__(self):
        super().__init__("custom_rule", "自定义验证规则")
    
    def validate(self, data):
        result = ValidationResult()
        # 实现自定义验证逻辑
        return result
```

## 📚 迁移指南

### 从v1.0迁移到v2.0

1. **无需修改现有代码** - 所有v1.0代码继续正常工作
2. **可选升级** - 逐步采用新的通用接口
3. **配置文件** - 将硬编码逻辑转换为配置文件
4. **新功能** - 利用插件化验证和多领域支持

### 迁移步骤

```python
# 步骤1：现有代码继续工作
from llmjson import LLMProcessor
processor = LLMProcessor(api_key="key")

# 步骤2：可选 - 使用新接口
from llmjson import ProcessorFactory
processor = ProcessorFactory.create_flood_disaster_processor(api_key="key")

# 步骤3：完全迁移 - 使用配置文件
processor = ProcessorFactory.create_processor("configs/flood_disaster.json")
```

## 🛠️ 开发和扩展

### 创建新的领域模板

1. **定义输出结构**（JSON Schema）
2. **设计实体和关系类型**
3. **编写提示模板**
4. **配置验证规则**
5. **测试和优化**

### 项目结构

```
llmjson/
├── templates/              # 模板系统
│   ├── base.py            # 模板基类
│   ├── legacy.py          # 兼容适配器
│   └── __init__.py
├── validators/            # 验证系统
│   ├── base.py           # 验证基类
│   ├── universal.py      # 通用验证器
│   └── rules/            # 验证规则
├── processors/           # 处理器系统
│   ├── universal.py      # 通用处理器
│   └── legacy.py         # 兼容适配器
├── factory.py            # 工厂类
└── __init__.py           # 主入口
```

## 📊 性能和监控

### 统计信息

```python
# 获取处理统计
stats = processor.get_stats()
print(f"成功率: {stats['success_rate']:.1f}%")
print(f"平均Token使用: {stats['avg_tokens_per_request']:.0f}")
print(f"总处理数: {stats['total_requests']}")
```

### 验证报告

```python
# 获取验证报告
result, info = processor.process_chunk(text, doc_name)
validation = info.get('validation', {})
print(f"验证错误: {len(validation.get('errors', []))}")
print(f"修正操作: {len(validation.get('corrections', []))}")
```

## 🧪 测试

运行测试脚本验证系统功能：

```bash
python test_universal_system.py
```

测试内容：
- ✅ 向后兼容性
- ✅ 新通用系统
- ✅ 模板创建
- ✅ 验证系统
- ✅ 配置系统

## 📖 文档和示例

- **设计文档**: `llmjson_universal_design.md` - 完整的架构设计
- **迁移指南**: `migration_guide.md` - 详细的迁移步骤
- **使用演示**: `demo_universal_usage.py` - 多领域使用示例
- **实现示例**: `example_universal_implementation.py` - 代码实现参考

## 🤝 贡献

欢迎贡献新的领域模板、验证规则和功能改进！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🆘 支持

- **GitHub Issues**: 报告问题和功能请求
- **文档**: 查看项目Wiki获取详细文档
- **示例**: 运行 `demo_universal_usage.py` 查看使用示例

---

**LLMJson 2.0 - 让信息抽取更简单、更通用、更强大！** 🚀