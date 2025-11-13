"""工具函数

提供通用的辅助功能。
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# 导入日志模块
from .log import (
    LogConfig,
    SingletonLogger,
    setup_logging,
    get_logger,
    create_logger_with_context
)


def ensure_dir(directory: str) -> str:
    """确保目录存在
    
    Args:
        directory: 目录路径
        
    Returns:
        目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return directory


def save_json(data: Any, file_path: str, ensure_ascii: bool = False, indent: int = 2):
    """保存JSON数据到文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        ensure_ascii: 是否确保ASCII编码
        indent: 缩进空格数
    """
    ensure_dir(os.path.dirname(file_path))
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)


def load_json(file_path: str) -> Any:
    """从文件加载JSON数据
    
    Args:
        file_path: 文件路径
        
    Returns:
        加载的数据
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        replacement: 替换字符
        
    Returns:
        清理后的文件名
    """
    import re
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    return re.sub(illegal_chars, replacement, filename)


def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 200) -> List[str]:
    """将文本分块
    
    Args:
        text: 原始文本
        chunk_size: 块大小（字符数）
        overlap: 重叠字符数
        
    Returns:
        文本块列表
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # 如果不是最后一块，尝试在句号或换行符处分割
        if end < len(text):
            # 向后查找合适的分割点
            for i in range(min(100, chunk_size // 10)):
                if end - i < start:
                    break
                if text[end - i] in '.。\n':
                    end = end - i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 计算下一个块的起始位置
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


class Timer:
    """简单的计时器类"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = datetime.now()
        self.end_time = None
    
    def stop(self):
        """停止计时"""
        self.end_time = datetime.now()
    
    def elapsed(self) -> float:
        """获取经过的时间（秒）"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    def elapsed_str(self) -> str:
        """获取格式化的经过时间"""
        seconds = self.elapsed()
        
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def merge_knowledge_graph_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    合并多个文档处理结果
    
    Args:
        results: 多个文档的处理结果列表
        
    Returns:
        合并后的知识图谱数据
    """
    all_entities = []
    all_states = []
    all_relations = []
    
    # 收集所有实体、状态和关系
    for result in results:
        all_entities.extend(result.get("基础实体", []))
        all_states.extend(result.get("状态实体", []))
        all_relations.extend(result.get("状态关系", []))
    
    # 去重
    unique_entities = _deduplicate_entities(all_entities)
    unique_states = _deduplicate_states(all_states)
    unique_relations = _deduplicate_relations(all_relations)
    
    # 组合最终结果
    return {
        "基础实体": unique_entities,
        "状态实体": unique_states,
        "状态关系": unique_relations
    }


def _deduplicate_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """去除重复的实体"""
    unique_entities = {}
    for entity in entities:
        entity_id = entity.get("唯一ID")
        if entity_id and entity_id not in unique_entities:
            unique_entities[entity_id] = entity
    return list(unique_entities.values())


def _deduplicate_states(states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """去除重复的状态"""
    unique_states = {}
    for state in states:
        state_id = state.get("状态ID")
        if state_id and state_id not in unique_states:
            unique_states[state_id] = state
    return list(unique_states.values())


def _deduplicate_relations(relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """去除重复的关系"""
    unique_relations = {}
    for relation in relations:
        # 用主体+关系+客体作为唯一键
        relation_key = f"{relation.get('主体状态ID')}|{relation.get('关系')}|{relation.get('客体状态ID')}"
        if relation_key not in unique_relations:
            unique_relations[relation_key] = relation
    return list(unique_relations.values())