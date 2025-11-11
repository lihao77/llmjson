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
pip install llm-json-generator
```

或从源码安装：

```bash
git clone https://github.com/lihao77/llm-json-generator.git
cd llm-json-generator
pip install -e .
```

### 基本使用

#### 1. 命令行工具（推荐）

**创建配置文件：**
```bash
llm-json-generator create-config --output config.json
```

**处理文本文件：**
```bash
# 处理纯文本文件
llm-json-generator process-text input.txt --config config.json --output results/

# 处理Word文档
llm-json-generator process-text document.docx --config config.json --streaming

# 处理模式由配置文件控制（enable_parallel和max_workers参数）
llm-json-generator process-text input.txt --chunk-size 3000
```

**数据验证：**
```bash
llm-json-generator validate data.json --schema schema.json --output validation_report.json
```

#### 2. Python API

```python
from llm_json_generator import (
    LLMProcessor, 
    ConfigManager, 
    DataValidator,
    WordChunker
)

# 创建配置
config = ConfigManager()
config.llm_config.api_key = "your-openai-api-key"
config.llm_config.model = "gpt-4o-mini"
config.processing_config.chunk_size = 2000

# 初始化处理器
processor = LLMProcessor(config)

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
  "llm_config": {
    "api_key": "your-openai-api-key",
    "base_url": "https://openrouter.ai/api/v1",
    "model": "deepseek/deepseek-chat-v3-0324:free",
    "temperature": 0.1,
    "max_tokens": 20000,
    "timeout": 60,
    "max_retries": 3,
    "retry_delay": 1.0
  },
  "processing_config": {
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
export LLM_MODEL="gpt-4o-mini"
export LLM_TEMPERATURE="0.1"
export CHUNK_SIZE="2000"
export MAX_WORKERS="4"
export ENABLE_PARALLEL="true"
```

### Word文档处理

```python
from llm_json_generator import WordChunker

# 创建Word分块器
chunker = WordChunker(
    max_tokens=2000,
    overlap_tokens=200
)

# 分块处理Word文档
chunks = chunker.chunk_document_with_tables("document.docx")

# 处理每个分块
for i, chunk in enumerate(chunks):
    result, info = processor.process_chunk(chunk, f"doc_chunk_{i}")
    if info['success']:
        print(f"块 {i+1} 处理成功")
```

### 批量和流式处理

```python
# 准备文档列表
documents = [
    ("doc1", 0, "第一个文档的内容..."),
    ("doc2", 0, "第二个文档的内容..."),
    # 更多文档...
]

# 批量处理
results = processor.batch_process(documents)
for result, info in results:
    if info['success']:
        print("处理成功")
    else:
        print(f"处理失败: {info['error']}")

# 流式处理（适合大量文档）
for result, info in processor.batch_process(documents):
    if info['success']:
        # 实时处理每个结果
        save_result(result)
```

### 数据验证

```python
from llm_json_generator import DataValidator

# 创建验证器
validator = DataValidator()

# 验证JSON数据
data = {"entities": [...], "relationships": [...]}
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
from llm_json_generator import PromptTemplate

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
from llm_json_generator import Timer

# 使用计时器
with Timer() as timer:
    result, info = processor.process_chunk(text, "doc")

print(f"处理耗时: {timer.elapsed:.2f}秒")

# 获取处理统计
stats = processor.get_processing_stats()
print(f"总处理时间: {stats['total_time']:.2f}秒")
print(f"成功率: {stats['success_rate']:.1%}")
```

## 📋 系统要求

- **Python**: 3.9+
- **操作系统**: Windows, macOS, Linux
- **内存**: 建议4GB+
- **网络**: 需要访问OpenAI API

## 📦 依赖包

- `openai>=1.35.0` - OpenAI API客户端
- `json-repair>=0.25.0` - JSON修复工具
- `python-docx>=1.1.0` - Word文档处理
- `tiktoken>=0.7.0` - Token计算
- `requests>=2.31.0` - HTTP请求

## 🛠️ 开发指南

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/lihao77/llm-json-generator.git
cd llm-json-generator

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 代码格式化
black llm_json_generator/
flake8 llm_json_generator/
```

### 项目结构

```
llm-json-generator/
├── llm_json_generator/          # 主包目录
│   ├── __init__.py             # 包初始化
│   ├── cli.py                  # 命令行接口
│   ├── config.py               # 配置管理
│   ├── processor.py            # 核心处理器
│   ├── validator.py            # 数据验证器
│   ├── prompt_template.py      # 提示模板
│   ├── word_chunker.py         # Word文档分块
│   ├── utils.py                # 工具函数
│   └── exceptions.py           # 异常定义
├── tests/                      # 测试文件
├── docs/                       # 文档
├── examples/                   # 示例代码
├── setup.py                    # 安装配置
├── requirements.txt            # 依赖列表
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

- **问题报告**: [GitHub Issues](https://github.com/lihao77/llm-json-generator/issues)
- **功能请求**: [GitHub Discussions](https://github.com/lihao77/llm-json-generator/discussions)
- **文档**: [项目Wiki](https://github.com/lihao77/llm-json-generator/wiki)
- **邮箱**: qingyuepei@foxmail.com

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**注意**: 使用本工具需要有效的OpenAI API密钥。请确保遵守相关服务条款和使用限制。