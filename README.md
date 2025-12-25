# LLMJson v2.0

基于大语言模型的知识图谱提取工具

## 🚀 特性

- **配置驱动**: 通过JSON配置文件定义提取规则
- **模板系统**: 灵活的YAML模板定义提取格式
- **通用处理器**: 支持任意领域的信息提取
- **验证系统**: 自动验证和修复提取结果
- **环境变量**: 安全的API密钥管理

## 📦 安装

```bash
pip install llmjson
```

## 🔧 快速开始

### 1. 设置环境变量

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"
```

### 2. 创建配置文件

```bash
python -c "from llmjson import TemplateFactory; TemplateFactory.create_universal_template('my_template.yaml')"
```

### 3. 使用代码

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
```

### 4. 使用CLI

```bash
# 创建配置
python simple_cli.py create-config

# 处理文档
python simple_cli.py process document.txt
```

## 📁 项目结构

```
llmjson/
├── factory.py          # 核心工厂类
├── processors/         # 处理器模块
├── templates/          # 模板系统
├── validators/         # 验证系统
├── log/               # 日志系统
└── utils.py           # 工具函数

configs/               # 配置文件
templates/             # 模板文件
example.py            # 使用示例
simple_cli.py         # 命令行工具
```

## 🔗 配置文件格式

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

## 📄 许可证

MIT License
