# GitHub 仓库设置指南

## 手动创建GitHub仓库步骤

### 1. 在GitHub上创建新仓库

1. 登录您的GitHub账户
2. 点击右上角的 "+" 图标，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `llm-json-generator`
   - **Description**: `一个用于大语言模型生成JSON数据的Python包`
   - **Public/Private**: 选择 Public（公开仓库）
   - **Initialize repository**: 不要勾选任何选项（不要添加README、.gitignore或License）
4. 点击 "Create repository"

### 2. 推送本地代码到GitHub

在创建仓库后，GitHub会显示推送现有代码的命令。以下是完整的推送步骤：

```bash
# 如果您还没有在json_generator目录中，请先进入
cd json_generator

# 添加远程仓库（请将 your-username 替换为您的GitHub用户名）
git remote add origin https://github.com/your-username/llm-json-generator.git

# 推送代码到GitHub
git branch -M master
git push -u origin master
```

### 3. 验证推送成功

推送完成后，您应该能在GitHub上看到您的代码。

## 后续步骤

### 创建发布版本

当您的代码准备好发布时，可以创建GitHub Release：

```bash
# 创建标签
git tag v1.0.0
git push origin v1.0.0
```

然后在GitHub上创建Release：
1. 进入您的仓库页面
2. 点击 "Releases"
3. 点击 "Create a new release"
4. 选择标签 `v1.0.0`
5. 填写发布说明
6. 点击 "Publish release"

### 配置GitHub Pages（可选）

如果您想为项目创建文档网站：

1. 进入仓库的 "Settings" 页面
2. 滚动到 "Pages" 部分
3. 选择源分支（通常是master）
4. 选择文件夹（通常是 `/root`）
5. 点击 "Save"

## 项目信息完善建议

### 1. 更新setup.py中的个人信息

在推送之前，请确保更新以下文件中的个人信息：

- `setup.py`: 更新作者姓名、邮箱、GitHub用户名
- `README.md`: 更新GitHub链接和联系信息
- `LICENSE`: 更新版权所有者姓名

### 2. 添加项目描述

在GitHub仓库的 "About" 部分添加项目描述：
- **Description**: 简短描述项目功能
- **Topics**: 添加相关标签，如 `python`, `llm`, `json`, `nlp`, `knowledge-graph`
- **Website**: 如果有文档网站，可以添加链接

### 3. 启用功能

考虑启用以下GitHub功能：
- **Issues**: 用于bug报告和功能请求
- **Discussions**: 用于社区讨论
- **Projects**: 用于项目管理
- **Wiki**: 用于文档（可选）

## 安装包发布到PyPI（可选）

如果您想将包发布到Python包索引（PyPI）：

```bash
# 安装构建工具
pip install build twine

# 构建包
python -m build

# 上传到测试PyPI
twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ llm-json-generator

# 上传到正式PyPI
twine upload dist/*
```

注意：上传PyPI需要注册账户并配置API token。