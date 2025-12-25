#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# 读取requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="llmjson",
    version="2.0.0",
    author="LLMJson Team",
    author_email="contact@llmjson.com",
    description="基于大语言模型的知识图谱提取工具",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/llmjson/llmjson",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    include_package_data=True,
    package_data={
        "llmjson": [
            "templates/*.yaml",
            "configs/*.json"
        ]
    },
    entry_points={
        "console_scripts": [
            "llmjson=simple_cli:main",
        ],
    },
    keywords="llm, knowledge graph, information extraction, nlp, ai",
    project_urls={
        "Bug Reports": "https://github.com/llmjson/llmjson/issues",
        "Source": "https://github.com/llmjson/llmjson",
        "Documentation": "https://llmjson.readthedocs.io/",
    },
)
