"""
通用模板系统

提供可配置的、领域无关的提示模板管理功能。
"""

from .base import BaseTemplate, ConfigurableTemplate

__all__ = [
    'BaseTemplate',
    'ConfigurableTemplate'
]