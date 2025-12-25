# LLMJson - 配置驱动的信息提取框架

LLMJson 是一个基于大语言模型的通用信息提取框架，支持通过配置文件定义提取规则和输出格式。

## 特性

- **配置驱动**: 通过YAML模板和JSON配置文件定义提取规则
- **通用架构**: 支持多种信息提取任务，从简单实体提取到复杂知识图谱构建
- **模板系统**: 灵活的模板变量系统，支持用户自定义示例
- **多API支持**: 兼容OpenAI API格式的各种服务（OpenAI、DeepSeek、本地模型等）
- **数据验证**: 基于JSON Schema的输出验证和自动修正

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

复制 `.env.example` 为 `.env` 并填入API配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# OpenAI API 配置
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# 或使用 DeepSeek API
# OPENAI_API_KEY=sk-your-deepseek-key
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# OPENAI_MODEL=deepseek-chat
```

### 3. 运行示例

```bash
python example.py
```

## 配置驱动使用方式

### 基本用法

```python
from llmjson import ProcessorFactory

# 使用配置文件创建处理器
processor = ProcessorFactory.create_processor("configs/universal_template.json")

# 处理文本
result, info = processor.process_chunk("张三在苹果公司工作", "示例文档")

if info['success']:
    print("提取结果:", result)
else:
    print("处理失败:", info['error'])
```

### 配置文件结构

**配置文件** (`configs/*.json`):
```json
{
  "template": {
    "config_path": "templates/universal.yaml"
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

**模板文件** (`templates/*.yaml`):
```yaml
name: "通用信息提取模板"
description: "可配置的通用信息提取模板"

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

# 用户定义的输出示例
output_example:
  entities:
    - type: "person"
      name: "张三"
      id: "P-张三-001"

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
```

## 内置配置

### 1. 通用信息提取 (`configs/universal_template.json`)

适用于一般的实体和关系提取任务。

### 2. 洪涝灾害专用 (`configs/flood_disaster_complete.json`)

专门用于洪涝灾害相关信息的结构化提取，包含：
- 基础实体（事件、地点、设施）
- 状态实体（独立状态、联合状态）
- 状态关系（触发、影响、调控、导致）

## 自定义配置

### 创建新的提取任务

1. **定义模板** (`templates/my_task.yaml`):
   - 设计输出数据结构 (`output_schema`)
   - 提供输出示例 (`output_example`)
   - 定义实体/关系类型
   - 编写提示模板

2. **创建配置** (`configs/my_task.json`):
   - 指向模板文件
   - 设置API参数

3. **使用配置**:
   ```python
   processor = ProcessorFactory.create_processor("configs/my_task.json")
   ```

## 模板变量系统

模板支持自动变量替换：

- `{entity_types}` - 自动生成实体类型描述
- `{relation_types}` - 自动生成关系类型描述  
- `{output_format_example}` - 自动生成输出格式示例
- `{doc_name}`, `{chunk}` - 运行时传入的文档信息

## API兼容性

支持所有兼容OpenAI API格式的服务：

- **OpenAI官方**: `https://api.openai.com/v1`
- **DeepSeek**: `https://api.deepseek.com/v1`
- **本地模型** (如Ollama): `http://localhost:11434/v1`
- **其他兼容服务**

## 许可证

MIT License