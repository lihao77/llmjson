"""
上下文日志器

提供带有上下文信息的日志功能。
"""

import logging
from typing import Dict, Any, Optional


class ContextLogger:
    """上下文日志器"""
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
        self.adapter = logging.LoggerAdapter(logger, context)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录调试信息"""
        self._log(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录信息"""
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录警告"""
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录错误"""
        self._log(logging.ERROR, message, extra)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录严重错误"""
        self._log(logging.CRITICAL, message, extra)
    
    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录异常"""
        merged_extra = self._merge_extra(extra)
        self.adapter.exception(message, extra=merged_extra)
    
    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """内部日志方法"""
        merged_extra = self._merge_extra(extra)
        
        # 将上下文信息添加到消息中以便显示
        context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
        if context_str:
            formatted_message = f"{message} [{context_str}]"
        else:
            formatted_message = message
            
        self.adapter.log(level, formatted_message, extra=merged_extra)
    
    def _merge_extra(self, extra: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """合并额外信息"""
        if extra is None:
            return {}
        return extra
    
    def update_context(self, new_context: Dict[str, Any]):
        """更新上下文"""
        self.context.update(new_context)
        self.adapter = logging.LoggerAdapter(self.logger, self.context)
    
    def get_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        return self.context.copy()


class TimedContextLogger(ContextLogger):
    """带时间统计的上下文日志器"""
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        super().__init__(logger, context)
        self.timers = {}
    
    def start_timer(self, timer_name: str):
        """开始计时"""
        import time
        self.timers[timer_name] = time.time()
        self.info(f"⏱️ 开始计时: {timer_name}")
    
    def end_timer(self, timer_name: str):
        """结束计时"""
        import time
        if timer_name not in self.timers:
            self.warning(f"计时器 {timer_name} 不存在")
            return
        
        elapsed = time.time() - self.timers[timer_name]
        self.info(f"⏱️ 计时结束: {timer_name}, 耗时: {elapsed:.2f}秒")
        del self.timers[timer_name]
        return elapsed
    
    def log_with_timing(self, timer_name: str, message: str, level: int = logging.INFO):
        """带计时的日志记录"""
        self.start_timer(timer_name)
        try:
            self._log(level, message)
            return True
        finally:
            self.end_timer(timer_name)
    
    def time_context(self, timer_name: str):
        """时间上下文管理器"""
        return TimerContext(self, timer_name)


class TimerContext:
    """计时器上下文管理器"""
    
    def __init__(self, timed_logger: 'TimedContextLogger', timer_name: str):
        self.timed_logger = timed_logger
        self.timer_name = timer_name
    
    def __enter__(self):
        self.timed_logger.start_timer(self.timer_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = self.timed_logger.end_timer(self.timer_name)
        return False


class StructuredLogger(ContextLogger):
    """结构化日志器"""
    
    def log_event(self, event_name: str, event_data: Dict[str, Any], level: int = logging.INFO):
        """记录结构化事件"""
        import json
        
        structured_data = {
            'event': event_name,
            'timestamp': self._get_timestamp(),
            'data': event_data
        }
        
        # 格式化事件数据以便显示
        data_str = json.dumps(event_data, ensure_ascii=False, separators=(',', ':'))
        message = f"事件: {event_name} -> {data_str}"
        self._log(level, message, extra=structured_data)
    
    def log_metrics(self, metrics: Dict[str, Any]):
        """记录指标数据"""
        self.log_event('metrics', metrics, logging.INFO)
    
    def log_performance(self, operation: str, duration: float, additional_data: Optional[Dict[str, Any]] = None):
        """记录性能数据"""
        perf_data = {
            'operation': operation,
            'duration_seconds': duration,
            'performance_level': self._classify_performance(duration)
        }
        
        if additional_data:
            perf_data.update(additional_data)
        
        self.log_event('performance', perf_data)
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _classify_performance(self, duration: float) -> str:
        """分类性能等级"""
        if duration < 1.0:
            return 'fast'
        elif duration < 5.0:
            return 'normal'
        elif duration < 10.0:
            return 'slow'
        else:
            return 'very_slow'
