#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM JSON Generator 包安装配置
"""

from setuptools import setup, find_packages
import os

# 读取README文件
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="llm-json-generator",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="一个用于大语言模型生成JSON数据的Python包",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/llm-json-generator",
    project_urls={
        "Bug Reports": "https://github.com/your-username/llm-json-generator/issues",
        "Source": "https://github.com/your-username/llm-json-generator",
        "Documentation": "https://github.com/your-username/llm-json-generator/wiki",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "llmgen=llm_json_generator.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="llm,json,generator,openai,knowledge-graph,nlp",
)