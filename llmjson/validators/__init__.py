"""
通用验证器系统

提供基于JSON Schema和自定义规则的数据验证功能。
"""

from .base import BaseValidator, ValidationRule, ValidationResult
from .universal import UniversalValidator
from .rules import *

__all__ = [
    'BaseValidator',
    'ValidationRule', 
    'ValidationResult',
    'UniversalValidator'
]