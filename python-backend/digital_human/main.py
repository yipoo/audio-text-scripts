import uvicorn
from digital_human.api.routes import app
from digital_human.config.config import API_CONFIG

def main():
    """启动数字人API服务"""
    try:
        print("正在启动数字人API服务...")
        uvicorn.run(
            app,
            host=API_CONFIG["host"],
            port=API_CONFIG["port"],
            log_level="info" if API_CONFIG.get("debug") else "error"
        )
    except Exception as e:
        print(f"启动服务失败: {str(e)}")
        raise

if __name__ == "__main__":
    main() 