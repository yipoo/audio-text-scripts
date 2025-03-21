#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import time
from datetime import datetime
from dotenv import load_dotenv

from ai_generation.content_creator import ContentCreator

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='生成多份含义相似但内容不同的话术')
    parser.add_argument('--input', '-i', type=str, help='输入文件路径，包含已识别的文本')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径', default=None)
    parser.add_argument('--num', '-n', type=int, help='生成的话术数量', default=10)
    return parser.parse_args()

def main():
    # 加载环境变量
    load_dotenv()
    
    args = parse_args()
    
    # 检查输入文件
    if not args.input:
        print("错误：请指定输入文件路径")
        sys.exit(1)
    
    if not os.path.exists(args.input):
        print(f"错误：输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 读取输入文件
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        
        if not text:
            print("错误：输入文件为空")
            sys.exit(1)
            
        print(f"已读取输入文件: {args.input}")
        print(f"文本长度: {len(text)} 字符")
        print(f"文本预览: {text[:100]}...")
    except Exception as e:
        print(f"读取输入文件时出错: {str(e)}")
        sys.exit(1)
    
    # 如果没有指定输出文件，自动生成
    if args.output is None:
        base_name = os.path.basename(args.input)
        name_without_ext = os.path.splitext(base_name)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"output/{name_without_ext}_scripts_{timestamp}.json"
    
    # 创建输出目录
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"将生成 {args.num} 份话术")
    print(f"输出文件: {args.output}")
    
    # 创建内容创作器
    try:
        creator = ContentCreator()
        
        # 生成话术
        scripts = []
        
        # 添加原始文本作为第一项
        scripts.append({
            "id": 0,
            "type": "原始文本",
            "content": text
        })
        
        for i in range(args.num):
            try:
                # 生成话术
                script = creator.generate_script(text)
                
                # 添加到结果列表
                scripts.append({
                    "id": i + 1,
                    "type": f"生成话术 {i+1}",
                    "content": script
                })
                
                # 输出进度
                print(f"已生成话术 {i+1}/{args.num}")
                
                # 每生成5份保存一次
                if (i + 1) % 5 == 0 or i + 1 == args.num:
                    # 保存到输出文件
                    with open(args.output, 'w', encoding='utf-8') as f:
                        json.dump(scripts, f, ensure_ascii=False, indent=2)
                    print(f"已保存当前进度到 {args.output}")
                    
            except Exception as e:
                print(f"生成第{i+1}份话术时出错: {str(e)}")
        
        print(f"\n成功生成 {len(scripts)-1} 份话术:")
        for i, script in enumerate(scripts):
            if i == 0:
                print(f"\n--- 原始文本 ---")
            else:
                print(f"\n--- 话术 {i} ---")
            
            preview = script['content'][:200] + "..." if len(script['content']) > 200 else script['content']
            print(preview)
            print("-" * 50)
        
        print(f"\n所有话术已保存至: {args.output}")
        
    except Exception as e:
        print(f"生成话术时出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
