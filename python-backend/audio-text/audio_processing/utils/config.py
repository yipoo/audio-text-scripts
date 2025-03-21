"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 阿里云配置
ALIYUN_ACCESS_KEY_ID = os.getenv('ALIYUN_ACCESS_KEY_ID', '')
ALIYUN_ACCESS_KEY_SECRET = os.getenv('ALIYUN_ACCESS_KEY_SECRET', '')
ALIYUN_APPKEY = os.getenv('ALIYUN_APPKEY', '')
ALIYUN_REGION = os.getenv('ALIYUN_REGION', 'cn-shanghai')

# 检查必要的配置
if not ALIYUN_ACCESS_KEY_ID or not ALIYUN_ACCESS_KEY_SECRET or not ALIYUN_APPKEY:
    print("警告：阿里云配置未设置，请设置以下环境变量：")
    print("- ALIYUN_ACCESS_KEY_ID")
    print("- ALIYUN_ACCESS_KEY_SECRET")
    print("- ALIYUN_APPKEY")
