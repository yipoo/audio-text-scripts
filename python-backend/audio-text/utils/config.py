"""
配置加载模块
"""
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# 导入项目根目录的配置
try:
    from config import OUTPUT_DIR, UPLOADS_DIR
except ImportError:
    # 如果导入失败，使用默认值
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
    UPLOADS_DIR = os.path.join(ROOT_DIR, "uploads")
    
    # 确保目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)

# 指定.env文件路径并加载环境变量
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"已加载环境变量文件: {env_path}")
else:
    # 尝试加载python-backend目录下的.env文件
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"已加载环境变量文件: {env_path}")
    else:
        # 尝试加载项目根目录下的.env文件
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"已加载环境变量文件: {env_path}")
        else:
            print("警告: 未找到.env文件，环境变量可能未正确加载")

# 阿里云API配置
ALIYUN_ACCESS_KEY_ID = os.getenv('ALIYUN_ACCESS_KEY_ID')
ALIYUN_ACCESS_KEY_SECRET = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
ALIYUN_REGION = os.getenv('ALIYUN_REGION', 'cn-shanghai')

# 阿里云语音识别配置
ALIYUN_APPKEY = os.getenv('ALIYUN_APPKEY')

# 阿里云DeepSeek模型配置
ALIYUN_DASHSCOPE_API_KEY = os.getenv('ALIYUN_DASHSCOPE_API_KEY')

def check_config(strict=False):
    """
    检查配置是否完整
    
    Args:
        strict: 是否严格检查。如果为True，则缺少配置会抛出异常；
               如果为False，则只会显示警告
    
    Returns:
        配置是否完整
    """
    required_vars = [
        'ALIYUN_ACCESS_KEY_ID', 
        'ALIYUN_ACCESS_KEY_SECRET', 
        'ALIYUN_APPKEY',
        'ALIYUN_DASHSCOPE_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not globals().get(var)]
    
    if missing_vars:
        message = f"缺少环境变量配置: {', '.join(missing_vars)}"
        if strict:
            raise ValueError(message)
        else:
            print(f"警告: {message}")
            print("某些功能可能无法正常工作。请参考.env.example配置环境变量。")
            
            # 询问是否继续
            if sys.stdin.isatty():  # 检查是否在交互式环境
                response = input("是否仍要继续? (y/n): ")
                if response.lower() != 'y':
                    sys.exit(0)
            
            return False
    
    return True

def get_config_status():
    """
    获取配置状态
    
    Returns:
        配置状态字典，包含每个配置项是否可用
    """
    config_vars = {
        'ALIYUN_ACCESS_KEY_ID': ALIYUN_ACCESS_KEY_ID is not None,
        'ALIYUN_ACCESS_KEY_SECRET': ALIYUN_ACCESS_KEY_SECRET is not None,
        'ALIYUN_REGION': ALIYUN_REGION is not None,
        'ALIYUN_APPKEY': ALIYUN_APPKEY is not None,
        'ALIYUN_DASHSCOPE_API_KEY': ALIYUN_DASHSCOPE_API_KEY is not None
    }
    
    return config_vars
