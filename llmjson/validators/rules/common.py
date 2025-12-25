"""
通用验证规则

提供常用的验证规则实现。
"""

from typing import Dict, Any, List, Set
from ..base import ValidationRule, ValidationResult, ValidationCorrection


class EntityRemovalCorrection(ValidationCorrection):
    """实体移除修正操作"""
    
    def __init__(self, indices_to_remove: List[int], entity_key: str = 'entities'):
        super().__init__(f"移除重复实体 (索引: {indices_to_remove})")
        self.indices_to_remove = sorted(indices_to_remove, reverse=True)
        self.entity_key = entity_key
    
    def apply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """应用修正"""
        corrected_data = data.copy()
        entities = corrected_data.get(self.entity_key, [])
        
        for index in self.indices_to_remove:
            if 0 <= index < len(entities):
                entities.pop(index)
        
        corrected_data[self.entity_key] = entities
        return corrected_data


class EntityDeduplicationRule(ValidationRule):
    """实体去重规则"""
    
    def __init__(self, similarity_threshold: float = 0.8, entity_key: str = 'entities'):
        super().__init__("entity_deduplication", "去除重复的实体")
        self.similarity_threshold = similarity_threshold
        self.entity_key = entity_key
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        
        entities = data.get(self.entity_key, [])
        if not entities:
            return result
        
        # 简单的名称相似度检查
        seen_names = set()
        duplicates = []
        
        for i, entity in enumerate(entities):
            name = self._get_entity_name(entity).lower().strip()
            if name in seen_names:
                duplicates.append(i)
                result.add_warning(f"发现重复实体: {self._get_entity_name(entity)}")
            else:
                seen_names.add(name)
        
        # 创建修正操作
        if duplicates:
            correction = EntityRemovalCorrection(duplicates, self.entity_key)
            result.add_correction(correction)
        
        return result
    
    def _get_entity_name(self, entity: Dict[str, Any]) -> str:
        """获取实体名称"""
        # 支持不同的名称字段
        for name_field in ['name', '名称', 'title', 'label']:
            if name_field in entity:
                return str(entity[name_field])
        return str(entity.get('id', ''))


class RelationValidationRule(ValidationRule):
    """关系验证规则"""
    
    def __init__(self, entity_key: str = 'entities', relation_key: str = 'relations'):
        super().__init__("relation_validation", "验证关系的有效性")
        self.entity_key = entity_key
        self.relation_key = relation_key
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        
        entities = data.get(self.entity_key, [])
        relations = data.get(self.relation_key, [])
        
        if not entities or not relations:
            return result
        
        # 收集所有实体ID
        entity_ids = set()
        for entity in entities:
            entity_id = self._get_entity_id(entity)
            if entity_id:
                entity_ids.add(entity_id)
        
        # 验证关系
        invalid_relations = []
        for i, relation in enumerate(relations):
            source = self._get_relation_source(relation)
            target = self._get_relation_target(relation)
            
            if source and source not in entity_ids:
                result.add_error(f"关系 {i} 的源实体 '{source}' 不存在")
                invalid_relations.append(i)
            
            if target and target not in entity_ids:
                result.add_error(f"关系 {i} 的目标实体 '{target}' 不存在")
                invalid_relations.append(i)
        
        # 可以添加移除无效关系的修正操作
        if invalid_relations:
            result.add_warning(f"发现 {len(invalid_relations)} 个无效关系")
        
        return result
    
    def _get_entity_id(self, entity: Dict[str, Any]) -> str:
        """获取实体ID"""
        for id_field in ['id', '唯一ID', 'entity_id']:
            if id_field in entity:
                return str(entity[id_field])
        return ""
    
    def _get_relation_source(self, relation: Dict[str, Any]) -> str:
        """获取关系源"""
        for source_field in ['source', '主体状态ID', 'source_id']:
            if source_field in relation:
                return str(relation[source_field])
        return ""
    
    def _get_relation_target(self, relation: Dict[str, Any]) -> str:
        """获取关系目标"""
        for target_field in ['target', '客体状态ID', 'target_id']:
            if target_field in relation:
                return str(relation[target_field])
        return ""


class TimeFormatValidationRule(ValidationRule):
    """时间格式验证规则"""
    
    def __init__(self, time_fields: List[str] = None):
        super().__init__("time_format_validation", "验证时间格式")
        self.time_fields = time_fields or ['time', '时间', 'date', 'timestamp']
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        
        # 递归检查所有时间字段
        self._validate_time_fields(data, result, "")
        
        return result
    
    def _validate_time_fields(self, obj: Any, result: ValidationResult, path: str):
        """递归验证时间字段"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                if key in self.time_fields and isinstance(value, str):
                    if not self._is_valid_time_format(value):
                        result.add_warning(f"时间格式可能不正确: {current_path} = '{value}'")
                
                self._validate_time_fields(value, result, current_path)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]"
                self._validate_time_fields(item, result, current_path)
    
    def _is_valid_time_format(self, time_str: str) -> bool:
        """检查时间格式是否有效"""
        import re
        
        # 支持多种时间格式
        patterns = [
            r'^\d{4}-\d{2}-\d{2}至\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD至YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
            r'^\d{4}年\d{1,2}月\d{1,2}日$',  # YYYY年MM月DD日
        ]
        
        for pattern in patterns:
            if re.match(pattern, time_str):
                return True
        
        return False