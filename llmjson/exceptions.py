"""自定义异常类

定义了LLM JSON生成器包中使用的自定义异常类。
"""


class LLMProcessingError(Exception):
    """LLM处理过程中的错误"""
    
    def __init__(self, message: str, error_code: str = None, original_error: Exception = None):
        super().__init__(message)
        self.error_code = error_code
        self.original_error = original_error
        self.message = message
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ValidationError(Exception):
    """数据验证过程中的错误"""
    
    def __init__(self, message: str, validation_type: str = None, invalid_data: dict = None):
        super().__init__(message)
        self.validation_type = validation_type
        self.invalid_data = invalid_data
        self.message = message
    
    def __str__(self):
        if self.validation_type:
            return f"[{self.validation_type}] {self.message}"
        return self.message


class APIConnectionError(LLMProcessingError):
    """API连接错误"""
    
    def __init__(self, message: str, api_endpoint: str = None):
        super().__init__(message, "API_CONNECTION_ERROR")
        self.api_endpoint = api_endpoint


class JSONParsingError(LLMProcessingError):
    """JSON解析错误"""
    
    def __init__(self, message: str, raw_response: str = None):
        super().__init__(message, "JSON_PARSING_ERROR")
        self.raw_response = raw_response


class PromptTemplateError(LLMProcessingError):
    """提示模板错误"""
    
    def __init__(self, message: str, template_name: str = None):
        super().__init__(message, "PROMPT_TEMPLATE_ERROR")
        self.template_name = template_name