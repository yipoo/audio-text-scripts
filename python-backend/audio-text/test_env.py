#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试环境配置是否正确
"""
import os
import sys
import importlib

def check_module(module_name):
    """检查模块是否可以导入"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        return False, str(e)

def main():
    """主函数"""
    # 检查是否在虚拟环境中运行
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    print(f"是否在虚拟环境中运行: {'是' if in_venv else '否'}")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查必要的模块
    modules = [
        "numpy", "jieba", "requests", "dotenv", 
        "sounddevice", "soundfile"
    ]
    
    print("\n模块检查:")
    # pydub不再是必须的，但仍然尝试导入
    try:
        import pydub
        print(f"  ✅ pydub 已安装 (版本: {pydub.__version__})")
    except ImportError as e:
        print(f"  ⚠️ pydub 未安装: {str(e)}")
        print("     这不是问题，程序已使用soundfile和numpy替代pydub功能")
    
    for module in modules:
        result = check_module(module)
        if result is True:
            print(f"  ✅ {module} 已安装")
        else:
            print(f"  ❌ {module} 安装失败: {result[1]}")
    
    # 检查项目目录结构
    print("\n目录结构检查:")
    directories = [
        "audio_processing", "text_processing", "ai_generation", 
        "utils", "recordings", "transcripts", "generated"
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"  ✅ {directory} 目录存在")
        else:
            print(f"  ❌ {directory} 目录不存在")
    
    print("\n环境检查完成！")

if __name__ == "__main__":
    main()
