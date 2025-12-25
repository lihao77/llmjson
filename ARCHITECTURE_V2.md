# LLMJson 2.0 架构设计说明

## 🎯 设计原则

### 1. **原有文件完全保留**
- ✅ `processor.py` - 原有的LLMProcessor继续使用
- ✅ `validator.py` - 原有的DataValidator继续使用  
- ✅ `prompt_template.py` - 原有的PromptTemplate继续使用
- ✅ 所有原有功能、优化和bug修复都保持

### 2. **增量式扩展**
- 🆕 新增通用系统作为**补充**，不是**替换**
- 🔄 提供多种使用方式，用户可以选择
- 📈 渐进式迁移，降低风险

### 3. **零破坏性变更**
- ✅ 原有代码无需任何修改
- ✅ 原有API接口完全保持
- ✅ 原有行为完全一致

## 🏗️ 架构层次

```
llmjson/
├── 📁 原有核心文件（继续使用）
│   ├── processor.py          # ✅ 原有LLMProcessor
│   ├── validator.py          # ✅ 原有DataValidator  
│   ├── prompt_template.py    # ✅ 原有PromptTemplate
│   └── ...                   # ✅ 其他原有文件
│
├── 📁 新增通用系统（可选使用）
│   ├── templates/            # 🆕 通用模板系统
│   │   ├── base.py          # 🆕 模板基类
│   │   └── legacy.py        # 🆕 洪涝灾害适配器
│   ├── validators/          # 🆕 通用验证系统
│   │   ├── universal.py     # 🆕 通用验证器
│   │   └── rules/           # 🆕 验证规则
│   ├── processors/          # 🆕 通用处理器
│   │   ├── universal.py     # 🆕 通用处理器
│   │   └── legacy.py        # 🆕 增强适配器
│   └── factory.py           # 🆕 工厂模式
│
└── __init__.py              # 🔄 统一入口
```

## 🚀 使用方式对比

### 方式1：原有系统（推荐，零风险）

```python
# 完全使用原有文件，没有任何变化
from llmjson import LLMProcessor, PromptTemplate, DataValidator

# 这里的LLMProcessor就是processor.py中的原有类
processor = LLMProcessor(api_key="your-key")
result, info = processor.process_chunk(text, 'doc.txt')

# ✅ 所有原有功能都在
# ✅ 所有原有优化都在  
# ✅ 所有原有bug修复都在
```

### 方式2：增强系统（原有 + 通用）

```python
# 使用增强版，继承自原有LLMProcessor
from llmjson import EnhancedLLMProcessor

# 默认行为与原有完全一致
processor = EnhancedLLMProcessor(api_key="your-key")
result, info = processor.process_chunk(text, 'doc.txt')  # 洪涝灾害模式

# 可选：动态切换到通用模式
from llmjson import ConfigurableTemplate
template = ConfigurableTemplate('templates/knowledge_graph.yaml')
processor.set_universal_template(template)
result, info = processor.process_chunk(text, 'doc.txt')  # 通用模式

# ✅ 包含所有原有功能
# 🆕 额外支持通用模板
# 🔄 可以动态切换模式
```

### 方式3：全新系统（纯通用）

```python
# 完全基于新的通用架构
from llmjson import ProcessorFactory

processor = ProcessorFactory.create_processor('config.json')
result, info = processor.process_chunk(text, 'doc.txt')

# 🆕 完全配置驱动
# 🆕 支持任意领域
# 🆕 插件化验证
```

## 🔍 实现细节

### 1. 原有文件保持不变

```python
# llmjson/__init__.py
from .processor import LLMProcessor          # ✅ 直接使用原有类
from .validator import DataValidator         # ✅ 直接使用原有类
from .prompt_template import PromptTemplate  # ✅ 直接使用原有类
```

### 2. 增强适配器继承原有类

```python
# llmjson/processors/legacy.py
from ..processor import LLMProcessor as OriginalLLMProcessor

class EnhancedLLMProcessor(OriginalLLMProcessor):
    """继承原有LLMProcessor，添加通用功能"""
    
    def __init__(self, **kwargs):
        # 调用原有初始化
        super().__init__(**kwargs)
        # 添加通用功能
        self.universal_template = None
        
    def process_chunk(self, chunk, doc_name):
        if self.universal_template:
            # 使用通用模式
            return self._process_chunk_universal(chunk, doc_name)
        else:
            # 使用原有逻辑
            return super().process_chunk(chunk, doc_name)
```

### 3. 工厂模式创建不同处理器

```python
# llmjson/factory.py
class ProcessorFactory:
    @staticmethod
    def create_flood_disaster_processor(**kwargs):
        # 返回原有的LLMProcessor
        return LLMProcessor(**kwargs)
    
    @staticmethod
    def create_processor(config_path):
        # 返回通用处理器
        return UniversalProcessor(...)
```

## 📊 兼容性矩阵

| 功能 | 原有系统 | 增强系统 | 全新系统 |
|------|---------|---------|---------|
| 洪涝灾害提取 | ✅ 完整 | ✅ 完整 | ✅ 通过配置 |
| 原有API | ✅ 100% | ✅ 100% | ❌ 新API |
| 原有优化 | ✅ 保持 | ✅ 保持 | ❌ 重新实现 |
| 通用模板 | ❌ 不支持 | ✅ 支持 | ✅ 原生支持 |
| 配置驱动 | ❌ 不支持 | ✅ 可选 | ✅ 原生支持 |
| 插件验证 | ❌ 不支持 | ✅ 可选 | ✅ 原生支持 |
| 迁移风险 | 🟢 无风险 | 🟡 低风险 | 🟠 中风险 |

## 🎯 推荐使用策略

### 对于现有项目
1. **继续使用原有系统** - 零风险，所有功能保持
2. **可选尝试增强系统** - 在测试环境验证新功能
3. **逐步迁移到全新系统** - 长期规划

### 对于新项目
1. **小项目** - 使用原有系统，简单可靠
2. **多领域项目** - 使用全新系统，充分利用通用性
3. **混合需求** - 使用增强系统，灵活切换

## 🔧 验证方法

运行测试脚本验证架构正确性：

```bash
python test_universal_system.py
```

测试内容：
- ✅ 原有文件是否被正确使用
- ✅ 原有功能是否完整保持
- ✅ 新增功能是否正常工作
- ✅ 兼容性是否完全保持

## 📈 未来规划

### 短期（1-3个月）
- 完善通用模板库
- 优化验证规则
- 收集用户反馈

### 中期（3-6个月）  
- 性能优化
- 更多领域支持
- 可视化配置工具

### 长期（6个月+）
- 考虑是否逐步迁移到全新架构
- 基于用户使用情况决定原有系统的维护策略
- 建立模板生态系统

这样的设计确保了**原有投资得到保护**，同时为**未来扩展提供了可能**。