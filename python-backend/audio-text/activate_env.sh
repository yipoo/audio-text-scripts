#!/bin/bash
# 激活虚拟环境的脚本

# 激活虚拟环境
source venv/bin/activate

# 显示当前Python路径
which python

# 显示当前Python版本
python --version

echo "虚拟环境已激活，您可以使用 'deactivate' 命令退出虚拟环境"
echo "使用 'pip install -r requirements.txt' 安装依赖"
