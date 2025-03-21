"""
配置文件 - 用于定义应用程序的全局配置
"""
import os

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 输出目录配置 - 存储处理结果
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")

# 上传目录配置 - 存储上传的音频文件
UPLOADS_DIR = os.path.join(ROOT_DIR, "uploads")

# 确保目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
