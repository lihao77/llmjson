# LLMJson v2.0 用户使用指南

## 📖 概述

LLMJson 是一个基于大语言模型的知识图谱提取工具，采用配置驱动的设计理念，支持任意领域的信息提取任务。本指南将带你从零开始，完成从配置创建、模板定制到运行提取的完整流程。

## 🚀 快速开始

### 第一步：安装

```bash
pip install llmjson
```

### 第二步：环境配置

1. **复制环境变量模板**
```bash
cp .env.example .env
```

2. **编辑 .env 文件**
```bash
# 必需配置
OPENAI_API_KEY=your-actual-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# 可选配置
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4000
```

### 第三步：验证安装

```bash
python example.py
```

如果看到 "✅ 配置驱动系统运行正常"，说明安装成功！

## 📋 完整使用流程

### 流程一：使用现有配置（推荐新手）

#### 1. 选择预设配置

项目提供了两个预设配置：

- **通用配置** (`configs/universal_template.json`)
  - 适用场景：人物、组织、地点等通用信息提取
  - 模板文件：`templates/universal.yaml`

- **洪涝灾害配置** (`configs/flood_disaster_complete.json`)
  - 适用场景：灾害事件、影响评估等专业信息提取
  - 模板文件：`templates/flood_disaster.yaml`

#### 2. 代码方式使用

```python
from llmjson import ProcessorFactory

# 创建处理器
processor = ProcessorFactory.create_processor("configs/universal_template.json")

# 处理文本
text = "张三在苹果公司工作，公司位于北京市。"
result, info = processor.process_chunk(text, "示例文档")

if info['success']:
    print("提取的实体:", result['entities'])
    print("提取的关系:", result['relations'])
else:
    print("处理失败:", info['error'])
```

#### 3. 命令行方式使用

```bash
# 处理单个文件
python simple_cli.py process document.txt -c configs/universal_template.json

# 结果会保存为 result_document.json
```

### 流程二：创建自定义配置

#### 1. 创建配置文件

```bash
# 使用CLI创建基础配置
python simple_cli.py create-config -o my_config.json
```

生成的配置文件结构：
```json
{
  "template": {
    "config_path": "templates/universal.yaml"
  },
  "validator": {},
  "processor": {
    "api_key": "${OPENAI_API_KEY}",
    "base_url": "${OPENAI_BASE_URL}",
    "model": "${OPENAI_MODEL}",
    "temperature": 0.1,
    "max_tokens": 4000,
    "timeout": 60,
    "max_retries": 3,
    "retry_delay": 1.0
  }
}
```

#### 2. 配置文件说明

- **template**: 指定使用的模板文件
- **validator**: 验证规则配置（可选）
- **processor**: LLM处理器参数
  - 支持环境变量替换 (`${变量名}`)
  - 可调整温度、最大token数等参数

### 流程三：创建自定义模板

#### 1. 模板文件结构

模板文件使用YAML格式，包含以下部分：

```yaml
name: "模板名称"
description: "模板描述"
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

# 输出示例
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
  你是专业的信息提取引擎...

user_prompt: |
  请从以下文本中提取信息：
  文档：{doc_name}
  内容：{chunk}
```

#### 2. 创建自定义模板示例

假设我们要创建一个"产品评论"提取模板：

```yaml
name: "产品评论信息提取"
description: "提取产品评论中的产品、用户、评价信息"
version: "2.0"

output_schema:
  type: "object"
  properties:
    products:
      type: "array"
      items:
        type: "object"
        properties:
          name: {type: "string"}
          brand: {type: "string"}
          category: {type: "string"}
    reviews:
      type: "array"
      items:
        type: "object"
        properties:
          user: {type: "string"}
          product: {type: "string"}
          rating: {type: "number"}
          comment: {type: "string"}

output_example:
  products:
    - name: "iPhone 15"
      brand: "苹果"
      category: "手机"
  reviews:
    - user: "张三"
      product: "iPhone 15"
      rating: 5
      comment: "很好用"

entity_types:
  - name: "product"
    description: "产品名称"
  - name: "user"
    description: "用户名称"
  - name: "review"
    description: "评论内容"

system_prompt: |
  你是专业的产品评论分析引擎。请从评论文本中提取产品信息和用户评价。
  
  输出格式：{output_format_example}

user_prompt: |
  请分析以下产品评论：
  
  来源：{doc_name}
  内容：{chunk}
```

#### 3. 使用自定义模板

1. 保存模板为 `templates/product_review.yaml`
2. 创建对应的配置文件：

```json
{
  "template": {
    "config_path": "templates/product_review.yaml"
  },
  "processor": {
    "api_key": "${OPENAI_API_KEY}",
    "base_url": "${OPENAI_BASE_URL}",
    "model": "${OPENAI_MODEL}",
    "temperature": 0.1
  }
}
```

3. 使用配置：

```python
processor = ProcessorFactory.create_processor("configs/product_review.json")
result, info = processor.process_chunk(review_text, "产品评论")
```

## 🔧 高级功能

### 1. 批量处理

```python
from llmjson import ProcessorFactory
import os

processor = ProcessorFactory.create_processor("configs/universal_template.json")

# 处理目录中的所有文本文件
input_dir = "documents"
output_dir = "results"

for filename in os.listdir(input_dir):
    if filename.endswith('.txt'):
        with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as f:
            text = f.read()
        
        result, info = processor.process_chunk(text, filename)
        
        if info['success']:
            output_file = os.path.join(output_dir, f"{filename}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
```

### 2. 自定义验证规则

```python
from llmjson.validators.base import ValidationRule, ValidationResult

class CustomValidationRule(ValidationRule):
    def validate(self, data):
        # 自定义验证逻辑
        if not data.get('entities'):
            return ValidationResult(
                is_valid=False,
                error_message="必须包含至少一个实体",
                corrected_data=None
            )
        return ValidationResult(is_valid=True)

# 在配置中使用
config = {
    "validator": {
        "custom_rules": [CustomValidationRule()]
    }
}
```

### 3. 环境变量管理

支持的环境变量：

```bash
# 必需
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# 可选
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4000
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=3
OPENAI_RETRY_DELAY=1.0
```

## 📊 实际应用示例

### 示例1：新闻文章信息提取

**场景**：从新闻文章中提取人物、事件、地点信息

**模板配置**：
```yaml
name: "新闻信息提取"
entity_types:
  - name: "person"
    description: "新闻中提到的人物"
  - name: "event"
    description: "新闻事件"
  - name: "location"
    description: "事件发生地点"
  - name: "organization"
    description: "相关组织机构"

relation_types:
  - name: "参与"
    description: "人物参与事件"
  - name: "发生于"
    description: "事件发生在某地"
```

**使用代码**：
```python
processor = ProcessorFactory.create_processor("configs/news_extraction.json")

news_text = """
北京时间12月25日，国家主席习近平在北京人民大会堂会见了来访的德国总理朔尔茨。
双方就中德关系发展等问题进行了深入交流。
"""

result, info = processor.process_chunk(news_text, "新闻报道")
```

### 示例2：学术论文信息提取

**场景**：从学术论文中提取作者、机构、研究方法等信息

**模板配置**：
```yaml
name: "学术论文信息提取"
entity_types:
  - name: "author"
    description: "论文作者"
  - name: "institution"
    description: "作者所属机构"
  - name: "method"
    description: "研究方法"
  - name: "dataset"
    description: "使用的数据集"
```

### 示例3：企业信息提取

**场景**：从企业介绍中提取公司信息、业务领域、关键人物等

**模板配置**：
```yaml
name: "企业信息提取"
entity_types:
  - name: "company"
    description: "公司名称"
  - name: "business"
    description: "业务领域"
  - name: "executive"
    description: "高管人员"
  - name: "product"
    description: "主要产品"
```

## 🛠️ 故障排除

### 常见问题

#### 1. API Key 错误
```
错误：Authentication failed
解决：检查 .env 文件中的 OPENAI_API_KEY 是否正确
```

#### 2. 模板文件不存在
```
错误：Template file not found
解决：检查配置文件中的 template.config_path 路径是否正确
```

#### 3. JSON 解析失败
```
错误：Failed to parse JSON response
解决：
1. 检查模板中的 output_example 格式是否正确
2. 降低 temperature 参数值
3. 增加 max_tokens 参数值
```

#### 4. 环境变量未设置
```
错误：Environment variable not set
解决：确保 .env 文件存在且包含必要的环境变量
```

### 调试技巧

#### 1. 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

processor = ProcessorFactory.create_processor("config.json")
```

#### 2. 检查处理信息
```python
result, info = processor.process_chunk(text, "test")
print("处理信息:", info)
print("原始响应:", info.get('raw_response'))
```

#### 3. 验证配置文件
```python
import json
with open('config.json', 'r') as f:
    config = json.load(f)
print("配置内容:", json.dumps(config, indent=2))
```

## 📚 最佳实践

### 1. 模板设计原则

- **明确性**：实体类型和关系定义要清晰明确
- **示例性**：提供完整、准确的输出示例
- **一致性**：保持命名和格式的一致性
- **完整性**：覆盖所有可能的输出情况

### 2. 配置管理建议

- **环境分离**：为开发、测试、生产环境创建不同配置
- **版本控制**：将配置文件纳入版本控制
- **敏感信息**：使用环境变量管理API密钥等敏感信息
- **文档化**：为每个配置文件添加说明注释

### 3. 性能优化建议

- **合理分块**：将长文本分割为适当大小的块
- **并发处理**：对于大量文档，使用多线程处理
- **缓存结果**：对于重复处理的文档，缓存结果
- **监控使用**：监控API调用次数和成本

### 4. 质量保证

- **结果验证**：定期检查提取结果的准确性
- **模板测试**：为每个模板创建测试用例
- **错误处理**：完善的错误处理和重试机制
- **日志记录**：记录处理过程中的关键信息

## 🔗 相关资源

- **项目文档**：`README.md`
- **架构说明**：`ARCHITECTURE.md`
- **更新日志**：`CHANGELOG.md`
- **示例代码**：`example.py`
- **CLI工具**：`simple_cli.py`

## 📞 技术支持

如果在使用过程中遇到问题：

1. 查看本指南的故障排除部分
2. 检查项目的 Issues 页面
3. 运行 `python example.py` 进行系统自检
4. 查看日志文件了解详细错误信息

---

**祝你使用愉快！LLMJson v2.0 让信息提取变得简单高效。**