"""
验证规则集合

提供各种通用的验证规则。
"""

from .common import EntityDeduplicationRule, RelationValidationRule
from .flood_disaster import FloodDisasterValidationRules

__all__ = [
    'EntityDeduplicationRule',
    'RelationValidationRule', 
    'FloodDisasterValidationRules'
]