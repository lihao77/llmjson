#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模板功能
"""

from pathlib import Path
from llmjson import ProcessorFactory

def test_load_template():
    """测试加载模板"""
    template_path = Path("templates/flood_disaster.yaml")
    template = ProcessorFactory._create_template({'config_path': str(template_path)})
    template_content = template.create_prompt(doc_name='测试名称', chunk='测试文档')
    
    print("生成的模板内容:")
    print(template_content)
    
    
    
if __name__ == "__main__":
    test_load_template()