#!/bin/bash

cd "$(dirname "$0")"

# 杀掉可能占用8000端口的进程
echo "正在检查并杀掉占用8000端口的进程..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# 激活audio-text目录中的虚拟环境
source audio-text/venv/bin/activate

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 添加 audio-text 目录到 PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/audio-text:$PYTHONPATH"

# 检查是否需要安装依赖
if [ "$1" == "--install" ] || [ ! -d "audio-text/venv/lib/python3.13/site-packages/fastapi" ]; then
  echo "安装依赖..."
  pip install -r requirements.txt
else
  echo "跳过依赖安装，使用 --install 参数强制安装"
fi

# 运行API服务器 - 使用python -m uvicorn而不是直接调用uvicorn命令
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 退出虚拟环境
deactivate
