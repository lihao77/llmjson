# LLM JSON Generator

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)[![PyPI Version](https://img.shields.io/badge/pypi-1.0.0-orange.svg)](#)

一个功能强大的Python包，专为使用大语言模型（LLM）生成结构化JSON数据而设计。支持文本分块、批量处理、流式处理、Word文档解析和数据验证等功能。

## ✨ 核心特性

- 🤖 **多LLM支持**: 支持OpenAI GPT系列等主流大语言模型
- 📄 **文档处理**: 支持纯文本和Word文档(.docx)处理
- ⚡ **高效处理**: 提供批量处理、流式处理和并行处理模式
- 🔧 **灵活配置**: 支持配置文件和环境变量配置
- ✅ **数据验证**: 内置JSON数据验证和修复功能
- 🎯 **智能分块**: 自动文本分块，支持重叠和表格处理
- 📊 **进度监控**: 实时处理进度和性能统计
- 🛠️ **CLI工具**: 提供完整的命令行接口
- 🔄 **错误恢复**: 自动重试和错误处理机制

## 🚀 快速开始

### 安装

```bash
pip install llmjson
```

或从源码安装：

```bash
git clone https://github.com/lihao77/llmjson.git
cd llmjson
pip install -e .
```

### 基本使用

#### 1. 命令行工具（推荐）

支持两个命令：`llmjson` 和 `llmgen`（简写形式）

**创建配置文件：**
```bash
llmjson create-config --output config.json
# 或者使用简写
llmgen create-config --output config.json
```

**处理文本文件：**
```bash
# 处理纯文本文件
llmjson process document.txt --config config.json --output results/

# 处理Word文档（包含表格）
llmjson process document.docx --config config.json --tables

# 开启数据验证
llmjson process input.txt --config config.json --validation

# 使用自定义提示模板
llmjson process document.txt --template my_template.txt

# 启用详细日志
llmjson process document.txt --config config.json --log
```

**批量处理文档文件夹：**
```bash
# 批量处理文件夹中的所有文档
llmjson process-documents /path/to/documents/ --config config.json

# 使用优化流式处理模式（默认）
llmjson process-documents /path/to/documents/ --mode optimized

# 使用传统批量处理模式
llmjson process-documents /path/to/documents/ --mode batch

# 包含表格并生成验证报告
llmjson process-documents /path/to/documents/ --tables --validation
```

**数据验证：**
```bash
# 验证JSON数据
llmjson validate data.json

# 保存验证后的数据
llmjson validate data.json --output cleaned_data.json

# 生成验证报告
llmjson validate data.json --report validation_report.json

# 同时保存数据和报告
llmjson validate data.json --output cleaned_data.json --report validation_report.json
```

#### 2. Python API

```python
from llmjson import (
    LLMProcessor,
    ConfigManager,
    DataValidator,
    WordChunker,
    PromptTemplate
)

# 方式1: 从配置文件加载
config = ConfigManager("config.json")
merged_config = config.get_merged_config()
processor = LLMProcessor(**merged_config)

# 方式2: 直接传参数初始化
processor = LLMProcessor(
    api_key="your-openai-api-key",
    base_url="https://api.openai.com/v1",
    model="gpt-4o-mini",
    temperature=0.1,
    max_tokens=4000,
    chunk_size=2000,
    chunk_overlap=200,
    max_workers=4,
    enable_parallel=True
)

# 处理文本
text = "你的文本内容..."
result, info = processor.process_chunk(text, "document_name")

if info['success']:
    print("处理成功！")
    print(result)
else:
    print(f"处理失败: {info['error']}")
```

## 📖 详细文档

### 配置管理

#### 配置文件示例 (config.json)

```json
{
  "llm": {
    "api_key": "your-openai-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini",
    "temperature": 0.1,
    "max_tokens": 4000,
    "timeout": 60,
    "max_retries": 3,
    "retry_delay": 1.0,
    "stream": false,
    "force_json": true,
    "extra_body": null
  },
  "processing": {
    "chunk_size": 2000,
    "chunk_overlap": 200,
    "max_workers": 4,
    "enable_parallel": true
  }
}
```

#### 环境变量配置

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"
export LLM_TEMPERATURE="0.1"
export LLM_MAX_TOKENS="4000"
export CHUNK_SIZE="2000"
export CHUNK_OVERLAP="200"
export MAX_WORKERS="4"
```

### Word文档处理

```python
from llmjson import WordChunker

# 创建Word分块器
chunker = WordChunker(
    max_tokens=2000,
    overlap_tokens=200
)

# 分块处理Word文档
chunks = chunker.chunk_document_with_tables("document.docx")

# 处理每个分块
for i, chunk in enumerate(chunks):
    # chunk 已经是字符串，直接处理
    result, info = processor.process_chunk(chunk, f"document_chunk_{i}")
    if info['success']:
        print(f"块 {i+1} 处理成功")
        print(f"提取的实体数: {len(result.get('entities', []))}")
        print(f"提取的关系数: {len(result.get('relations', []))}")
```

### 批量处理

```python
# 准备文档块列表 (doc_name, chunk_index, chunk_content)
chunk_items = [
    ("doc1", 0, "第一个文档第一块的内容..."),
    ("doc1", 1, "第一个文档第二块的内容..."),
    ("doc2", 0, "第二个文档第一块的内容..."),
]

# 批量处理
results = processor.batch_process(chunk_items)
for result, info in results:
    if info['success']:
        print(f"文档 {info['doc_name']} 块 {info['chunk_index']} 处理成功")
        print(result)
    else:
        print(f"处理失败: {info['error']}")
```

### 使用 DocumentProcessor 处理完整文档

```python
from llmjson import DocumentProcessor

# 初始化文档处理器
doc_processor = DocumentProcessor(
    config_path="config.json",
    template_file=None  # 可选：自定义提示模板文件
)

# 处理单个文档
result = doc_processor.process_single_document(
    document_path="document.docx",
    base_output_dir="output",
    include_tables=True,
    generate_validation_report=True
)

if result['success']:
    print(f"✅ 处理成功！耗时: {result['processing_time']:.2f}秒")
    print(f"📦 文本块数: {result['chunks']['total']}")
    print(f"✅ 成功: {result['chunks']['successful']}")
    print(f"🏷️ 提取实体: {result['entities']['total']}个")
    print(f"🔗 提取关系: {result['relations']['total']}个")
```

### 数据验证

```python
from llmjson import DataValidator

# 创建验证器
validator = DataValidator()

# 验证JSON数据
data = {"entities": [], "relationships": []}
summary, full_report = validator.validate_data(data)

print(f"验证摘要: {summary}")
print(f"错误数量: {full_report['error_count']}")
print(f"修正数量: {full_report['correction_count']}")

# 导出验证报告
validator.export_validation_report("validation_report.json")
```

## 🔧 高级功能

### 自定义提示模板

```python
from llmjson import PromptTemplate

# 创建自定义模板
template = PromptTemplate(
    system_prompt="你是一个专业的知识图谱构建助手...",
    user_prompt="请从以下文本中提取实体和关系：\n{text}",
)

# 使用自定义模板
processor = LLMProcessor(config, prompt_template=template)
```

### 性能监控

```python
from llmjson import Timer

# 使用计时器
timer = Timer()
timer.start()

result, info = processor.process_chunk(text, "doc")

timer.stop()
print(f"处理耗时: {timer.elapsed():.2f}秒")
print(f"格式化时间: {timer.elapsed_str()}")

# 或使用上下文管理器
with Timer() as timer:
    result, info = processor.process_chunk(text, "doc")
print(f"处理耗时: {timer.elapsed():.2f}秒")

# 获取处理统计
stats = processor.get_stats()
print(f"总请求数: {stats['total_requests']}")
print(f"成功数: {stats['successful_requests']}")
print(f"失败数: {stats['failed_requests']}")
print(f"总Token数: {stats['total_tokens_used']}")
print(f"JSON解析错误: {stats['json_parsing_errors']}")
```

## 📋 系统要求

- **Python**: 3.9+
- **操作系统**: Windows, macOS, Linux
- **内存**: 建议4GB+
- **网络**: 需要访问OpenAI API或其他LLM服务

## 📦 依赖包

**核心依赖：**
- `openai>=1.35.0` - OpenAI API客户端
- `json-repair>=0.25.0` - JSON修复工具
- `python-docx>=1.1.0` - Word文档处理
- `tiktoken>=0.7.0` - Token计算
- `requests>=2.31.0` - HTTP请求
- `typing-extensions>=4.0.0` - 类型注解扩展

**可选依赖（用于开发）：**
- `pytest>=7.0.0` - 单元测试
- `pytest-cov>=4.0.0` - 测试覆盖率
- `black>=22.0.0` - 代码格式化
- `flake8>=5.0.0` - 代码检查
- `mypy>=1.0.0` - 类型检查

## 🛠️ 开发指南

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/lihao77/llmjson.git
cd llmjson

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 代码格式化
black llmjson/
flake8 llmjson/
```

### 项目结构

```
llmjson/
├── llmjson/          # 主包目录
│   ├── __init__.py             # 包初始化
│   ├── cli.py                  # 命令行接口
│   ├── config.py               # 配置管理
│   ├── processor.py            # 核心处理器
│   ├── validator.py            # 数据验证器
│   ├── prompt_template.py      # 提示模板
│   ├── word_chunker.py         # Word文档分块
│   ├── run_mode.py             # 文档处理运行模式
│   ├── utils.py                # 工具函数
│   ├── exceptions.py           # 异常定义
│   └── log/                    # 日志系统
│       ├── __init__.py
│       ├── config.py
│       ├── context.py
│       ├── manager.py
│       └── setup.py
├── setup.py                    # 安装配置
├── requirements.txt            # 依赖列表
├── pyproject.toml              # 项目配置
├── README.md                   # 项目说明
└── LICENSE                     # 许可证
```

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 使用 Black 进行代码格式化
- 使用 Flake8 进行代码检查
- 使用 MyPy 进行类型检查
- 编写单元测试覆盖新功能
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🆘 支持与反馈

- **问题报告**: [GitHub Issues](https://github.com/lihao77/llmjson/issues)
- **功能请求**: [GitHub Discussions](https://github.com/lihao77/llmjson/discussions)
- **文档**: [项目Wiki](https://github.com/lihao77/llmjson/wiki)
- **邮箱**: qingyuepei@foxmail.com

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**注意**: 使用本工具需要有效的OpenAI API密钥。请确保遵守相关服务条款和使用限制。