"""
验证器基类

定义验证系统的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple


class ValidationResult:
    """验证结果"""
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.corrections = []
    
    def add_error(self, message: str):
        """添加错误"""
        self.is_valid = False
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)
    
    def add_correction(self, correction: 'ValidationCorrection'):
        """添加修正操作"""
        self.corrections.append(correction)


class ValidationCorrection:
    """验证修正操作基类"""
    
    def __init__(self, description: str):
        self.description = description
    
    def apply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """应用修正"""
        raise NotImplementedError


class ValidationRule:
    """验证规则基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """执行验证"""
        raise NotImplementedError


class BaseValidator(ABC):
    """验证器基类"""
    
    def __init__(self):
        self.validation_report = {}
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """验证数据"""
        pass
    
    def get_validation_report(self) -> Dict[str, Any]:
        """获取验证报告"""
        return self.validation_report
    
    def reset_validation_report(self):
        """重置验证报告"""
        self.validation_report = {
            "errors": [],
            "warnings": [],
            "corrections": [],
            "schema_validation": True,
            "custom_validation": True
        }