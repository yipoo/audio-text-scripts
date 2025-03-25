import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)

# 导入并运行主程序
if __name__ == "__main__":
    try:
        from digital_human.main import main
        print("正在启动数字人服务...")
        main()
    except ImportError as e:
        print(f"导入错误: {str(e)}")
        print(f"当前Python路径: {sys.path}")
    except Exception as e:
        print(f"启动失败: {str(e)}") 