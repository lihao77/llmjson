"""
验证规则集合

提供各种通用的验证规则。
"""

from .common import EntityDeduplicationRule, RelationValidationRule

__all__ = [
    'EntityDeduplicationRule',
    'RelationValidationRule'
]