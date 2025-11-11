#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新日志模块演示脚本

展示重构后的日志系统的各种功能和最佳实践。
"""

import os
import sys
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from llm_json_generator.log import (
        LogConfig,
        SingletonLogger,
        setup_logging,
        get_logger,
        create_logger_with_context,
        create_timed_logger,
        create_structured_logger,
        setup_environment_logging,
        setup_from_config_file,
        log_function_call,
        log_execution_time
    )
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保模块路径正确")
    sys.exit(1)


def demo_basic_logging():
    """演示基本日志功能"""
    print("=" * 60)
    print("📝 基本日志功能演示")
    print("=" * 60)
    
    # 使用默认配置
    logger = setup_logging(log_level="DEBUG")
    
    logger.debug("🔍 这是一个调试信息")
    logger.info("ℹ️ 这是一个信息日志")
    logger.warning("⚠️ 这是一个警告")
    logger.error("❌ 这是一个错误")
    
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception("💥 捕获到异常")
    
    print("\n✅ 基本日志演示完成\n")


def demo_custom_config():
    """演示自定义配置"""
    print("=" * 60)
    print("⚙️ 自定义配置演示")
    print("=" * 60)
    
    # 创建自定义配置
    config = LogConfig()
    config.log_level = "INFO"
    config.max_file_size = 5 * 1024 * 1024  # 5MB
    config.backup_count = 3
    config.separate_error_log = True
    config.auto_cleanup = True
    config.enable_json = False  # 使用普通格式便于演示
    
    # 重置单例以便使用新配置
    singleton = SingletonLogger()
    singleton.reset()
    
    # 使用自定义配置
    logger = setup_logging(config=config)
    
    logger.info("🎛️ 使用自定义配置的日志")
    logger.info(f"📊 最大文件大小: {config.max_file_size // 1024 // 1024}MB")
    logger.info(f"📦 备份文件数: {config.backup_count}")
    
    print("\n✅ 自定义配置演示完成\n")


def demo_context_logging():
    """演示上下文日志"""
    print("=" * 60)
    print("🏷️ 上下文日志演示")
    print("=" * 60)
    
    # 创建带上下文的日志器
    context = {
        'user_id': 'user_123',
        'session_id': 'session_456',
        'operation': 'document_processing'
    }
    
    context_logger = create_logger_with_context(context)
    
    context_logger.info("开始处理文档")
    context_logger.info("文档处理中...")
    context_logger.error("遇到处理错误")
    context_logger.info("文档处理完成")
    
    # 更新上下文
    context_logger.update_context({'progress': '100%', 'result': 'success'})
    context_logger.info("最终状态更新")
    
    print("\n✅ 上下文日志演示完成\n")


def demo_timed_logging():
    """演示计时日志"""
    print("=" * 60)
    print("⏱️ 计时日志演示")
    print("=" * 60)
    
    context = {'operation': 'data_processing'}
    timed_logger = create_timed_logger(context)
    
    # 演示计时功能
    timed_logger.start_timer("process_data")
    timed_logger.info("开始处理数据...")
    
    # 模拟一些处理时间
    time.sleep(2)
    
    timed_logger.info("处理中...")
    time.sleep(1)
    
    elapsed = timed_logger.end_timer("process_data")
    timed_logger.info(f"数据处理完成，总耗时: {elapsed:.2f}秒")
    
    print("\n✅ 计时日志演示完成\n")


def demo_structured_logging():
    """演示结构化日志"""
    print("=" * 60)
    print("📋 结构化日志演示")
    print("=" * 60)
    
    context = {'service': 'document_processor'}
    structured_logger = create_structured_logger(context)
    
    # 记录事件
    structured_logger.log_event('user_login', {
        'user_id': 'user_123',
        'login_method': 'oauth',
        'ip_address': '192.168.1.100'
    })
    
    # 记录指标
    structured_logger.log_metrics({
        'documents_processed': 150,
        'processing_time_avg': 2.5,
        'success_rate': 0.95
    })
    
    # 记录性能数据
    structured_logger.log_performance('document_parsing', 1.8, {
        'document_size': 1024,
        'pages': 10
    })
    
    print("\n✅ 结构化日志演示完成\n")


def demo_environment_configs():
    """演示环境配置"""
    print("=" * 60)
    print("🌍 环境配置演示")
    print("=" * 60)
    
    environments = ['development', 'testing', 'production']
    
    for env in environments:
        print(f"\n--- {env.upper()} 环境 ---")
        
        # 重置单例
        singleton = SingletonLogger()
        singleton.reset()
        
        # 设置环境日志
        logger = setup_environment_logging(env)
        logger.info(f"在 {env} 环境中运行")
        logger.info(f"当前日志级别适用于 {env} 环境")
        
        if env == 'development':
            logger.debug("开发环境可以看到调试信息")
        elif env == 'production':
            logger.info("生产环境专注于重要信息")
    
    print("\n✅ 环境配置演示完成\n")


@log_function_call()
def sample_function_with_logging(x, y):
    """带日志装饰器的示例函数"""
    logger = get_logger()
    logger.info(f"计算 {x} + {y}")
    result = x + y
    logger.info(f"结果: {result}")
    return result


@log_execution_time()
def sample_slow_function():
    """带执行时间日志的慢函数"""
    logger = get_logger()
    logger.info("开始执行耗时操作...")
    time.sleep(1.5)  # 模拟耗时操作
    logger.info("耗时操作完成")
    return "completed"


def demo_decorators():
    """演示日志装饰器"""
    print("=" * 60)
    print("🎭 日志装饰器演示")
    print("=" * 60)
    
    # 确保有基础日志配置
    logger = get_logger()
    
    # 测试函数调用装饰器
    result = sample_function_with_logging(10, 20)
    logger.info(f"装饰器测试结果: {result}")
    
    # 测试执行时间装饰器
    result = sample_slow_function()
    logger.info(f"慢函数执行结果: {result}")
    
    print("\n✅ 装饰器演示完成\n")


def worker_function(worker_id: int, iterations: int = 5):
    """工作线程函数"""
    logger = get_logger()
    
    for i in range(iterations):
        logger.info(f"🧵 Worker {worker_id} - 任务 {i+1}/{iterations}")
        time.sleep(0.2)
    
    logger.info(f"✅ Worker {worker_id} 完成所有任务")
    return f"worker_{worker_id}_completed"


def demo_threading_safety():
    """演示线程安全性"""
    print("=" * 60)
    print("🔄 线程安全性演示")
    print("=" * 60)
    
    # 初始化日志系统
    logger = setup_logging(log_level="INFO")
    logger.info("开始多线程测试")
    
    # 创建多个线程
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(worker_function, i+1, 3) 
            for i in range(3)
        ]
        
        # 等待所有任务完成
        results = []
        for future in futures:
            result = future.result()
            results.append(result)
    
    logger.info(f"多线程测试完成，结果: {results}")
    print("\n✅ 线程安全性演示完成\n")


def demo_json_logging():
    """演示JSON格式日志"""
    print("=" * 60)
    print("📄 JSON格式日志演示")
    print("=" * 60)
    
    # 创建JSON格式配置
    config = LogConfig()
    config.enable_json = True
    config.log_level = "INFO"
    
    # 重置并使用JSON配置
    singleton = SingletonLogger()
    singleton.reset()
    
    logger = setup_logging(config=config)
    
    logger.info("这是JSON格式的日志")
    logger.warning("JSON格式便于机器处理")
    logger.error("错误信息也会以JSON格式输出")
    
    print("\n✅ JSON格式日志演示完成\n")


def demo_config_file():
    """演示配置文件功能"""
    print("=" * 60)
    print("📁 配置文件演示")
    print("=" * 60)
    
    # 创建示例配置文件
    config = LogConfig()
    config.log_level = "DEBUG"
    config.enable_json = False
    config.max_file_size = 1024 * 1024  # 1MB
    
    config_file = "demo_logging_config.json"
    config.save_to_json_file(config_file)
    
    print(f"配置文件已保存到: {config_file}")
    
    # 从配置文件加载
    singleton = SingletonLogger()
    singleton.reset()
    
    logger = setup_from_config_file(config_file)
    logger.info("使用配置文件初始化的日志")
    logger.debug("配置文件中的调试级别生效")
    
    # 清理配置文件
    if os.path.exists(config_file):
        os.remove(config_file)
        print(f"清理配置文件: {config_file}")
    
    print("\n✅ 配置文件演示完成\n")


def demo_error_handling():
    """演示错误处理"""
    print("=" * 60)
    print("💣 错误处理演示")
    print("=" * 60)
    
    logger = get_logger()
    
    # 模拟各种错误场景
    try:
        # 除零错误
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.exception("捕获到除零错误")
    
    try:
        # 文件不存在错误
        with open("nonexistent_file.txt", 'r') as f:
            content = f.read()
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
    
    try:
        # 类型错误
        result = "字符串" + 123
    except TypeError as e:
        logger.exception("类型错误")
    
    logger.info("错误处理演示完成，所有错误都被正确记录")
    print("\n✅ 错误处理演示完成\n")


def main():
    """主函数"""
    print("🎉 新日志模块全功能演示")
    print("=" * 60)
    
    try:
        # 运行各种演示
        demo_basic_logging()
        demo_custom_config()
        demo_context_logging()
        demo_timed_logging()
        demo_structured_logging()
        demo_environment_configs()
        demo_decorators()
        demo_threading_safety()
        demo_json_logging()
        demo_config_file()
        demo_error_handling()
        
        print("🎊 所有演示完成！")
        print("\n📁 请查看 logs/ 目录中的日志文件:")
        
        logs_dir = "logs"
        if os.path.exists(logs_dir):
            total_size = 0
            file_count = 0
            for file in sorted(os.listdir(logs_dir)):
                if file.endswith('.log') or '.log.' in file:
                    filepath = os.path.join(logs_dir, file)
                    size = os.path.getsize(filepath)
                    total_size += size
                    file_count += 1
                    print(f"   📄 {file} ({size:,} bytes)")
            
            print(f"\n📊 统计信息:")
            print(f"   文件数量: {file_count}")
            print(f"   总大小: {total_size:,} bytes ({total_size/1024:.2f} KB)")
        
        print("\n🔍 演示功能特点:")
        print("   ✅ 单例模式确保全局一致性")
        print("   ✅ 多种配置选项")
        print("   ✅ 上下文和结构化日志")
        print("   ✅ 自动日志轮转")
        print("   ✅ 线程安全")
        print("   ✅ JSON格式支持")
        print("   ✅ 装饰器便捷使用")
        print("   ✅ 环境配置支持")
        print("   ✅ 异常处理")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
