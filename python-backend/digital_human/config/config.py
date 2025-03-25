import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 数据目录
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
CACHE_DIR = ROOT_DIR / "cache"

# 创建必要的目录
for dir_path in [DATA_DIR, MODELS_DIR, CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 模型配置
MODEL_CONFIG = {
    "text_to_speech": {
        "model_name": "microsoft/speecht5_tts",  # 更换为可用的模型
        "vocoder_name": "microsoft/speecht5_hifigan",
        "cache_dir": str(CACHE_DIR / "tts"),
        "device": "mps",  # 将 "cpu" 改为 "mps" 启用 Apple Silicon GPU
        "language": "zh"  # 设置默认语言为中文
    }
}

# API配置
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8001,
    "debug": True
}

# 音频配置
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "audio_max_length": 30  # 秒
}

# 视频配置
VIDEO_CONFIG = {
    "frame_rate": 25,
    "resolution": (512, 512),  # (width, height)
    "video_max_length": 30  # 秒
}

# 缓存配置
CACHE_CONFIG = {
    "max_size": 1024 * 1024 * 1024,  # 1GB
    "ttl": 3600  # 1小时
} 