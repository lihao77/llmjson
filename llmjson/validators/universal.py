"""
通用验证器

基于JSON Schema和自定义规则的通用数据验证器。
"""

from typing import Dict, Any, List, Optional, Tuple
import jsonschema
from .base import BaseValidator, ValidationRule


class UniversalValidator(BaseValidator):
    """通用数据验证器，基于JSON Schema"""
    
    def __init__(self, schema: Dict[str, Any], custom_rules: Optional[List[ValidationRule]] = None):
        super().__init__()
        self.schema = schema
        self.custom_rules = custom_rules or []
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """验证数据"""
        self.reset_validation_report()
        validated_data = data.copy()
        
        # 1. JSON Schema验证
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            self.validation_report["schema_validation"] = False
            self.validation_report["errors"].append(f"Schema validation failed: {e.message}")
        
        # 2. 自定义规则验证
        for rule in self.custom_rules:
            try:
                rule_result = rule.validate(validated_data)
                if not rule_result.is_valid:
                    self.validation_report["custom_validation"] = False
                    self.validation_report["errors"].extend(rule_result.errors)
                
                self.validation_report["warnings"].extend(rule_result.warnings)
                
                # 应用修正
                for correction in rule_result.corrections:
                    validated_data = correction.apply(validated_data)
                    self.validation_report["corrections"].append(correction.description)
                    
            except Exception as e:
                self.validation_report["errors"].append(f"Custom rule '{rule.name}' failed: {str(e)}")
        
        return validated_data, self.validation_report


class LegacyValidatorAdapter(BaseValidator):
    """原有验证器的适配器，保持兼容性"""
    
    def __init__(self):
        super().__init__()
        # 导入原有的验证器
        from ..validator import DataValidator
        self._legacy_validator = DataValidator()
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """使用原有验证器进行验证"""
        validated_data, legacy_report = self._legacy_validator.validate_data(data)
        
        # 转换报告格式
        self.validation_report = self._convert_legacy_report(legacy_report)
        
        return validated_data, self.validation_report
    
    def _convert_legacy_report(self, legacy_report: Dict[str, Any]) -> Dict[str, Any]:
        """将原有报告格式转换为新格式"""
        return {
            "errors": legacy_report.get("errors_deleted", []),
            "warnings": legacy_report.get("warnings_unmodified", []),
            "corrections": legacy_report.get("warnings_modified", []),
            "schema_validation": len(legacy_report.get("errors_deleted", [])) == 0,
            "custom_validation": True,
            "legacy_report": legacy_report
        }