"""
通用处理器系统

提供可配置的、领域无关的信息抽取处理器。
"""

from .universal import UniversalProcessor
from .legacy import LegacyProcessorAdapter

__all__ = [
    'UniversalProcessor',
    'LegacyProcessorAdapter'
]