"""
洪涝灾害专用验证规则

保持与原有洪涝灾害验证逻辑的兼容性。
"""

from typing import Dict, Any, List
from ..base import ValidationRule, ValidationResult
from .common import EntityDeduplicationRule, RelationValidationRule, TimeFormatValidationRule


class FloodDisasterValidationRules:
    """洪涝灾害验证规则集合"""
    
    @staticmethod
    def get_all_rules() -> List[ValidationRule]:
        """获取所有洪涝灾害验证规则"""
        return [
            # 基础实体验证
            EntityDeduplicationRule(entity_key='基础实体'),
            FloodEntityTypeValidationRule(),
            FloodEntityIdFormatRule(),
            
            # 状态实体验证
            EntityDeduplicationRule(entity_key='状态实体'),
            FloodStateValidationRule(),
            TimeFormatValidationRule(),
            
            # 关系验证
            RelationValidationRule(entity_key='状态实体', relation_key='状态关系'),
            FloodRelationTypeValidationRule(),
        ]


class FloodEntityTypeValidationRule(ValidationRule):
    """洪涝灾害实体类型验证"""
    
    def __init__(self):
        super().__init__("flood_entity_type_validation", "验证洪涝灾害实体类型")
        self.allowed_types = ["事件", "地点", "设施"]
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        
        entities = data.get('基础实体', [])
        for i, entity in enumerate(entities):
            entity_type = entity.get('类型')
            if entity_type not in self.allowed_types:
                result.add_error(f"基础实体 {i} 的类型 '{entity_type}' 不在允许列表中: {self.allowed_types}")
        
        return result


class FloodEntityIdFormatRule(ValidationRule):
    """洪涝灾害实体ID格式验证"""
    
    def __init__(self):
        super().__init__("flood_entity_id_format", "验证洪涝灾害实体ID格式")
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        
        entities = data.get('基础实体', [])
        for i, entity in enumerate(entities):
            entity_id = entity.get('唯一ID', '')
            entity_type = entity.get('类型', '')
            
            if not self._is_valid_id_format(entity_id, entity_type):
                result.add_warning(f"基础实体 {i} 的ID格式可能不正确: '{entity_id}'")
        
        return result
    
    def _is_valid_id_format(self, entity_id: str, entity_type: str) -> bool:
        """检查ID格式是否正确"""
        import re
        
        if entity_type == "事件":
            # E-<行政区划码>-<日期YYYYMMDD>-<事件类型>
            pattern = r'^E-[A-Za-z0-9]+(-[0-9]{8})?-[A-Z_]+$'
        elif entity_type == "地点":
            # L-<行政区划码>[>子区域] 或 L-<实体类型>-<名称>[>区段]
            pattern = r'^L-([A-Za-z0-9]+)(>[^-]+)?$|^L-([A-Z_]+)-([^>]+)(>[^-]+)?$'
        elif entity_type == "设施":
            # F-<行政区划码>-<设施名称>
            pattern = r'^F-[A-Za-z0-9]+-.+$'
        else:
            return False
        
        return bool(re.match(pattern, entity_id))


class FloodStateValidationRule(ValidationRule):
    """洪涝灾害状态实体验证"""
    
    def __init__(self):
        super().__init__("flood_state_validation", "验证洪涝灾害状态实体")
        self.allowed_state_types = ["独立状态", "联合状态"]
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        
        states = data.get('状态实体', [])
        for i, state in enumerate(states):
            state_type = state.get('类型')
            entity_ids = state.get('关联实体ID列表', [])
            
            # 验证状态类型
            if state_type not in self.allowed_state_types:
                result.add_error(f"状态实体 {i} 的类型 '{state_type}' 不在允许列表中")
            
            # 验证关联实体数量
            if state_type == "独立状态" and len(entity_ids) != 1:
                result.add_warning(f"独立状态 {i} 应该只关联一个实体，当前关联 {len(entity_ids)} 个")
            
            if state_type == "联合状态" and len(entity_ids) < 2:
                result.add_warning(f"联合状态 {i} 应该关联多个实体，当前关联 {len(entity_ids)} 个")
        
        return result


class FloodRelationTypeValidationRule(ValidationRule):
    """洪涝灾害关系类型验证"""
    
    def __init__(self):
        super().__init__("flood_relation_type_validation", "验证洪涝灾害关系类型")
        self.allowed_relations = ["触发", "影响", "调控", "导致"]
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        
        relations = data.get('状态关系', [])
        for i, relation in enumerate(relations):
            relation_type = relation.get('关系')
            if relation_type not in self.allowed_relations:
                result.add_warning(f"状态关系 {i} 的类型 '{relation_type}' 不在允许列表中: {self.allowed_relations}")
        
        return result