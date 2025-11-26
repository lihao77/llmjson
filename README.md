# LLM JSON Generator

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)[![PyPI Version](https://img.shields.io/badge/pypi-1.0.0-orange.svg)](#)

[中文文档](README_zh.md) | English

A powerful Python package designed for generating structured JSON data using Large Language Models (LLMs). Supports text chunking, batch processing, streaming, Word document parsing, and data validation.

## ✨ Key Features

- 🤖 **Multi-LLM Support**: Compatible with mainstream large language models like OpenAI GPT series
- 📄 **Document Processing**: Supports plain text and Word document (.docx) processing
- ⚡ **Efficient Processing**: Provides batch processing, streaming, and parallel processing modes
- 🔧 **Flexible Configuration**: Supports configuration files and environment variables
- ✅ **Data Validation**: Built-in JSON data validation and repair functionality
- 🎯 **Smart Chunking**: Automatic text chunking with overlap and table processing support
- 📊 **Progress Monitoring**: Real-time processing progress and performance statistics
- 🛠️ **CLI Tools**: Complete command-line interface
- 🔄 **Error Recovery**: Automatic retry and error handling mechanisms

## 🚀 Quick Start

### Installation

```bash
pip install llmjson
```

Or install from source:

```bash
git clone https://github.com/lihao77/llmjson.git
cd llmjson
pip install -e .
```

### Basic Usage

#### 1. Command Line Tool (Recommended)

Supports two commands: `llmjson` and `llmgen` (shorthand)

**Create configuration file:**
```bash
llmjson create-config --output config.json
# Or use shorthand
llmgen create-config --output config.json
```

**Process text files:**
```bash
# Process plain text file
llmjson process document.txt --config config.json --output results/

# Process Word document (including tables)
llmjson process document.docx --config config.json --tables

# Enable data validation
llmjson process input.txt --config config.json --validation

# Use custom prompt template
llmjson process document.txt --template my_template.txt

# Enable verbose logging
llmjson process document.txt --config config.json --log
```

**Batch process document folders:**
```bash
# Batch process all documents in a folder
llmjson process-documents /path/to/documents/ --config config.json

# Use optimized streaming mode (default)
llmjson process-documents /path/to/documents/ --mode optimized

# Use traditional batch processing mode
llmjson process-documents /path/to/documents/ --mode batch

# Include tables and generate validation report
llmjson process-documents /path/to/documents/ --tables --validation
```

**Data validation:**
```bash
# Validate JSON data
llmjson validate data.json

# Save validated data
llmjson validate data.json --output cleaned_data.json

# Generate validation report
llmjson validate data.json --report validation_report.json

# Save both data and report
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

# Method 1: Load from configuration file
config = ConfigManager("config.json")
merged_config = config.get_merged_config()
processor = LLMProcessor(**merged_config)

# Method 2: Initialize with direct parameters
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

# Process text
text = "Your text content..."
result, info = processor.process_chunk(text, "document_name")

if info['success']:
    print("Processing successful!")
    print(result)
else:
    print(f"Processing failed: {info['error']}")
```

## 📖 Detailed Documentation

### Configuration Management

#### Configuration File Example (config.json)

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

#### Environment Variable Configuration

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

### Word Document Processing

```python
from llmjson import WordChunker

# Create Word chunker
chunker = WordChunker(
    max_tokens=2000,
    overlap_tokens=200
)

# Chunk Word document
chunks = chunker.chunk_document_with_tables("document.docx")

# Process each chunk
for i, chunk in enumerate(chunks):
    # chunk is already a string, process directly
    result, info = processor.process_chunk(chunk, f"document_chunk_{i}")
    if info['success']:
        print(f"Chunk {i+1} processed successfully")
        print(f"Entities extracted: {len(result.get('entities', []))}")
        print(f"Relations extracted: {len(result.get('relations', []))}")
```

### Batch Processing

```python
# Prepare document chunk list (doc_name, chunk_index, chunk_content)
chunk_items = [
    ("doc1", 0, "Content of first chunk of first document..."),
    ("doc1", 1, "Content of second chunk of first document..."),
    ("doc2", 0, "Content of first chunk of second document..."),
]

# Batch process
results = processor.batch_process(chunk_items)
for result, info in results:
    if info['success']:
        print(f"Document {info['doc_name']} chunk {info['chunk_index']} processed successfully")
        print(result)
    else:
        print(f"Processing failed: {info['error']}")
```

### Using DocumentProcessor for Complete Documents

```python
from llmjson import DocumentProcessor

# Initialize document processor
doc_processor = DocumentProcessor(
    config_path="config.json",
    template_file=None  # Optional: custom prompt template file
)

# Process single document
result = doc_processor.process_single_document(
    document_path="document.docx",
    base_output_dir="output",
    include_tables=True,
    generate_validation_report=True
)

if result['success']:
    print(f"✅ Processing successful! Time: {result['processing_time']:.2f}s")
    print(f"📦 Text chunks: {result['chunks']['total']}")
    print(f"✅ Successful: {result['chunks']['successful']}")
    print(f"🏷️ Entities extracted: {result['entities']['total']}")
    print(f"🔗 Relations extracted: {result['relations']['total']}")
```

### Data Validation

```python
from llmjson import DataValidator

# Create validator
validator = DataValidator()

# Validate JSON data
data = {"entities": [], "relationships": []}
summary, full_report = validator.validate_data(data)

print(f"Validation summary: {summary}")
print(f"Error count: {full_report['error_count']}")
print(f"Correction count: {full_report['correction_count']}")

# Export validation report
validator.export_validation_report("validation_report.json")
```

## 🔧 Advanced Features

### Custom Prompt Templates

```python
from llmjson import PromptTemplate

# Create custom template
template = PromptTemplate(
    system_prompt="You are a professional knowledge graph construction assistant...",
    user_prompt="Please extract entities and relations from the following text:\n{text}",
)

# Use custom template
processor = LLMProcessor(config, prompt_template=template)
```

### Performance Monitoring

```python
from llmjson import Timer

# Use timer
timer = Timer()
timer.start()

result, info = processor.process_chunk(text, "doc")

timer.stop()
print(f"Processing time: {timer.elapsed():.2f}s")
print(f"Formatted time: {timer.elapsed_str()}")

# Or use context manager
with Timer() as timer:
    result, info = processor.process_chunk(text, "doc")
print(f"Processing time: {timer.elapsed():.2f}s")

# Get processing statistics
stats = processor.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Successful: {stats['successful_requests']}")
print(f"Failed: {stats['failed_requests']}")
print(f"Total tokens: {stats['total_tokens_used']}")
print(f"JSON parsing errors: {stats['json_parsing_errors']}")
```

## 📋 System Requirements

- **Python**: 3.9+
- **Operating System**: Windows, macOS, Linux
- **Memory**: 4GB+ recommended
- **Network**: Requires access to OpenAI API or other LLM services

## 📦 Dependencies

**Core Dependencies:**
- `openai>=1.35.0` - OpenAI API client
- `json-repair>=0.25.0` - JSON repair tool
- `python-docx>=1.1.0` - Word document processing
- `tiktoken>=0.7.0` - Token calculation
- `requests>=2.31.0` - HTTP requests
- `typing-extensions>=4.0.0` - Type annotation extensions

**Optional Dependencies (for development):**
- `pytest>=7.0.0` - Unit testing
- `pytest-cov>=4.0.0` - Test coverage
- `black>=22.0.0` - Code formatting
- `flake8>=5.0.0` - Code linting
- `mypy>=1.0.0` - Type checking

## 🛠️ Development Guide

### Development Environment Setup

```bash
# Clone repository
git clone https://github.com/lihao77/llmjson.git
cd llmjson

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Code formatting
black llmjson/
flake8 llmjson/
```

### Project Structure

```
llmjson/
├── llmjson/          # Main package directory
│   ├── __init__.py             # Package initialization
│   ├── cli.py                  # Command line interface
│   ├── config.py               # Configuration management
│   ├── processor.py            # Core processor
│   ├── validator.py            # Data validator
│   ├── prompt_template.py      # Prompt template
│   ├── word_chunker.py         # Word document chunker
│   ├── run_mode.py             # Document processing run modes
│   ├── utils.py                # Utility functions
│   ├── exceptions.py           # Exception definitions
│   └── log/                    # Logging system
│       ├── __init__.py
│       ├── config.py
│       ├── context.py
│       ├── manager.py
│       └── setup.py
├── setup.py                    # Installation configuration
├── requirements.txt            # Dependency list
├── pyproject.toml              # Project configuration
├── README.md                   # Project documentation
└── LICENSE                     # License
```

## 🤝 Contributing

We welcome community contributions! Please follow these steps:

1. Fork the project repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

### Code Standards

- Use Black for code formatting
- Use Flake8 for code linting
- Use MyPy for type checking
- Write unit tests covering new features
- Update relevant documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support and Feedback

- **Issue Reporting**: [GitHub Issues](https://github.com/lihao77/llmjson/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/lihao77/llmjson/discussions)
- **Documentation**: [Project Wiki](https://github.com/lihao77/llmjson/wiki)
- **Email**: qingyuepei@foxmail.com

## 🙏 Acknowledgments

Thanks to all developers and users who have contributed to this project!

---

**Note**: Using this tool requires a valid OpenAI API key. Please ensure compliance with relevant terms of service and usage restrictions.
