#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量处理recordings文件夹中的所有音频文件
1. 将mp4文件转换为wav格式
2. 处理所有wav文件（语音转文字）
3. 为每个处理后的文件生成多份话术

使用方法:
    python process_all.py [选项]

选项:
    --num-scripts, -n INT    为每个文件生成的话术数量（默认：10）
    --keep-mp4, -k           保留原始MP4文件（默认会删除）
    --output-dir, -o DIR     指定输出目录（默认：output）
    --recursive, -r          递归搜索子目录（默认只搜索根目录）
    --async-generation, -a   异步生成多份话术（后台执行）
    --only-file FILE         只处理指定的文件

示例:
    # 处理所有文件，每个生成5份话术
    python process_all.py --num-scripts 5
    
    # 处理所有文件，保留原始MP4文件
    python process_all.py --keep-mp4
    
    # 指定自定义输出目录
    python process_all.py --output-dir my_output
    
    # 递归搜索子目录
    python process_all.py --recursive
    
    # 异步生成多份话术（后台执行）
    python process_all.py --async-generation
    
    # 只处理指定文件
    python process_all.py --only-file recordings/文件名.mp4
"""
import os
import sys
import subprocess
import glob
import argparse
from datetime import datetime
import time
import tqdm  # 导入tqdm用于显示进度条
import shutil

def convert_mp4_to_wav(mp4_file, wav_file):
    """将mp4文件转换为wav格式"""
    cmd = [
        "ffmpeg",
        "-i", mp4_file,
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", "16000",
        wav_file,
        "-y"  # 覆盖已存在的文件
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"转换失败: {str(e)}")
        return False

def process_audio_file(audio_file, output_dir):
    """处理音频文件（语音转文字、分段、创作）"""
    cmd = [
        sys.executable,
        "main.py",
        "process-file",
        "--input", audio_file,
        "--output-dir", output_dir
    ]
    
    print(f"\n📝 处理文件: {os.path.basename(audio_file)}")
    print(f"1️⃣ 语音转写中... ", end="", flush=True)
    
    try:
        # 使用Popen捕获实时输出
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True, 
            bufsize=1,
            universal_newlines=True
        )
        
        # 实时处理输出
        for line in process.stdout:
            # 如果是进度信息，直接输出到终端
            if "音频转写进度" in line:
                print(f"\r1️⃣ {line.strip()}", end="", flush=True)
            # 如果是分段信息
            elif "文本分段" in line:
                print(f"\r2️⃣ 文本分段中... ", end="", flush=True)
            # 如果是创作信息
            elif "内容创作" in line:
                print(f"\r3️⃣ 内容创作中... ", end="", flush=True)
        
        # 等待进程结束
        process.wait()
        
        # 检查返回码
        if process.returncode == 0:
            print("\r1️⃣ 语音转写完成 ✅")
            print(f"2️⃣ 文本分段完成 ✅")
            print(f"3️⃣ 内容创作完成 ✅")
            print(f"✅ 文件 {os.path.basename(audio_file)} 处理成功")
            return True
        else:
            stderr = process.stderr.read()
            print("\r1️⃣ 语音转写失败 ❌")
            
            # 将错误信息写入日志文件
            error_log = os.path.join(output_dir, "error.log")
            with open(error_log, 'w', encoding='utf-8') as f:
                f.write(f"命令: {' '.join(cmd)}\n")
                f.write(f"错误码: {process.returncode}\n")
                f.write(f"标准输出:\n{' '.join([line for line in process.stdout])}\n")
                f.write(f"错误输出:\n{stderr}\n")
            
            print(f"❌ 文件 {os.path.basename(audio_file)} 处理失败")
            print(f"错误日志已保存到: {error_log}")
            
            # 检查是否有部分处理结果
            transcript_file = os.path.join(output_dir, "transcript.txt")
            if os.path.exists(transcript_file) and os.path.getsize(transcript_file) > 0:
                print(f"注意: 转写结果已保存到 {transcript_file}，但后续处理失败")
                
                # 尝试继续处理
                try:
                    print("尝试继续处理转写结果...")
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    if text and len(text) > 0:
                        # 手动调用分段和创作
                        print(f"2️⃣ 文本分段中... ", end="", flush=True)
                        segment_cmd = [
                            sys.executable,
                            "main.py",
                            "segment",
                            "--input", transcript_file,
                            "--output", os.path.join(output_dir, "segments.json")
                        ]
                        
                        try:
                            subprocess.run(segment_cmd, check=True)
                            print("✅")
                            
                            # 继续处理创作
                            print(f"3️⃣ 内容创作中... ", end="", flush=True)
                            create_cmd = [
                                sys.executable,
                                "main.py",
                                "create",
                                "--input", os.path.join(output_dir, "segments.json"),
                                "--output", os.path.join(output_dir, "generated.json")
                            ]
                            
                            subprocess.run(create_cmd, check=True)
                            print("✅")
                            print(f"✅ 内容创作成功")
                            return True
                        except subprocess.CalledProcessError as e2:
                            print("❌")
                            print(f"❌ 继续处理失败: {str(e2)}")
                except Exception as e3:
                    print("❌")
                    print(f"❌ 尝试继续处理时出错: {str(e3)}")
            
            return False
    except Exception as e:
        print("❌")
        print(f"❌ 处理失败: {str(e)}")
        return False

def generate_multiple_scripts(transcript_file, output_file, num_scripts=10):
    """生成多份话术"""
    cmd = [
        sys.executable,
        "generate_multiple_scripts.py",
        "--input", transcript_file,
        "--output", output_file,
        "--num", str(num_scripts)
    ]
    
    print(f"\n🔄 生成{num_scripts}份话术...")
    
    try:
        # 显示进度条
        with tqdm.tqdm(total=num_scripts, desc="生成话术", unit="份") as pbar:
            # 创建进程
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时更新进度条
            for line in process.stdout:
                if "已生成话术" in line:
                    try:
                        current = int(line.split("已生成话术")[1].split("/")[0].strip())
                        pbar.update(current - pbar.n)
                    except:
                        pass
            
            # 等待进程结束
            process.wait()
            
            # 检查返回码
            if process.returncode != 0:
                stderr = process.stderr.read()
                print(f"❌ 生成话术失败: {stderr}")
                return False
                
        print(f"✅ 成功生成{num_scripts}份话术")
        return True
    except Exception as e:
        print(f"❌ 生成话术失败: {str(e)}")
        return False

def generate_scripts_async(transcript_file, output_file, num_scripts=10, output_dir=None):
    """异步生成多份话术（后台执行）"""
    cmd = [
        sys.executable,
        "generate_multiple_scripts.py",
        "--input", transcript_file,
        "--output", output_file,
        "--num", str(num_scripts)
    ]
    
    try:
        # 使用nohup在后台运行，并将输出重定向到日志文件
        log_file = os.path.join(output_dir, "scripts_generation.log")
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=f,
                preexec_fn=os.setpgrp  # 使进程在后台运行
            )
        
        print(f"✅ 已启动{num_scripts}份话术的后台生成任务")
        print(f"📝 日志文件: {log_file}")
        return True
    except Exception as e:
        print(f"❌ 启动后台生成话术任务失败: {str(e)}")
        return False

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="批量处理音频文件")
    parser.add_argument("--num-scripts", type=int, default=10, help="生成的话术数量，默认10")
    parser.add_argument("--keep-mp4", action="store_true", help="保留MP4文件，默认会删除")
    parser.add_argument("--output-dir", help="输出目录，默认为output")
    parser.add_argument("--recursive", "-r", action="store_true", help="递归处理子目录")
    parser.add_argument("--async-generation", "-a", action="store_true", help="异步生成话术，不等待生成完成")
    parser.add_argument("--only-file", help="只处理指定的文件")
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 设置输出目录
    output_dir = args.output_dir or "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 如果指定了只处理某个文件
    if args.only_file:
        if not os.path.exists(args.only_file):
            print(f"错误: 文件 {args.only_file} 不存在")
            return
        
        print(f"只处理指定文件: {args.only_file}")
        
        # 确定输出目录
        rel_path = os.path.relpath(args.only_file, "recordings")
        file_dir = os.path.dirname(rel_path)
        file_name = os.path.basename(args.only_file)
        file_name_no_ext = os.path.splitext(file_name)[0]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_output_dir = os.path.join(output_dir, file_dir, f"{file_name_no_ext}_{timestamp}")
        
        # 创建输出目录
        os.makedirs(file_output_dir, exist_ok=True)
        
        # 处理文件
        success = process_audio_file(args.only_file, file_output_dir)
        
        # 如果处理成功且需要生成多份话术
        if success and args.num_scripts > 0:
            transcript_file = os.path.join(file_output_dir, "transcript.txt")
            scripts_file = os.path.join(file_output_dir, "scripts.json")
            
            if args.async_generation:
                # 异步生成话术
                generate_scripts_async(transcript_file, scripts_file, args.num_scripts, file_output_dir)
            else:
                # 同步生成话术
                generate_multiple_scripts(transcript_file, scripts_file, args.num_scripts)
        
        print(f"\n处理完成！")
        if success:
            print(f"输出结果保存在 {file_output_dir} 目录下")
        return
    
    # 目录设置
    recordings_dir = "recordings"
    output_base_dir = output_dir
    
    # 确保输出目录存在
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)
    
    # 获取所有mp4和wav文件
    if args.recursive:
        # 递归搜索所有子目录
        mp4_files = []
        wav_files = []
        for root, _, files in os.walk(recordings_dir):
            for file in files:
                if file.endswith('.mp4'):
                    mp4_files.append(os.path.join(root, file))
                elif file.endswith('.wav'):
                    wav_files.append(os.path.join(root, file))
        print(f"递归搜索模式：搜索所有子目录")
    else:
        # 只搜索根目录
        mp4_files = glob.glob(os.path.join(recordings_dir, "*.mp4"))
        wav_files = glob.glob(os.path.join(recordings_dir, "*.wav"))
    
    # 转换所有mp4文件为wav
    converted_files = []
    if mp4_files:
        print(f"找到{len(mp4_files)}个MP4文件，开始转换...")
        for mp4_file in mp4_files:
            base_name = os.path.basename(mp4_file)
            file_name = os.path.splitext(base_name)[0]
            # 保持原始文件的目录结构
            mp4_dir = os.path.dirname(mp4_file)
            wav_file = os.path.join(mp4_dir, f"{file_name}.wav")
            
            print(f"转换文件: {mp4_file} -> {wav_file}")
            if convert_mp4_to_wav(mp4_file, wav_file):
                converted_files.append(wav_file)
                print(f"✅ 转换成功: {wav_file}")
                
                # 如果不保留MP4文件，则删除
                if not args.keep_mp4:
                    os.remove(mp4_file)
                    print(f"🗑️ 已删除原始MP4文件: {mp4_file}")
            else:
                print(f"❌ 转换失败: {mp4_file}")
    
    # 更新wav文件列表（包括新转换的文件）
    wav_files = list(set(wav_files + converted_files))
    
    if not wav_files:
        print("错误: recordings目录中没有找到任何wav文件，也没有可转换的mp4文件")
        return
    
    print(f"\n找到{len(wav_files)}个WAV文件，开始处理...")
    
    # 处理每个wav文件
    processed_count = 0
    for i, wav_file in enumerate(wav_files):
        # 保持与recordings目录相同的结构
        rel_path = os.path.relpath(wav_file, recordings_dir)
        rel_dir = os.path.dirname(rel_path)
        file_name = os.path.splitext(os.path.basename(wav_file))[0]
        
        # 创建对应的输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if rel_dir:
            # 如果文件在子目录中，保持相同的目录结构
            output_dir = os.path.join(output_base_dir, rel_dir, f"{file_name}_{timestamp}")
        else:
            # 如果文件在根目录中
            output_dir = os.path.join(output_base_dir, f"{file_name}_{timestamp}")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_dir), exist_ok=True)
        
        print(f"\n[{i+1}/{len(wav_files)}] 处理文件: {wav_file}")
        print(f"输出目录: {output_dir}")
        
        # 1. 处理音频文件（语音转文字）
        if process_audio_file(wav_file, output_dir):
            print(f"✅ 文件 {wav_file} 处理完成")
            
            # 2. 生成多份话术
            transcript_file = os.path.join(output_dir, "transcript.txt")
            if os.path.exists(transcript_file):
                scripts_output_file = os.path.join(output_dir, "scripts.json")
                print(f"为 {os.path.basename(transcript_file)} 生成{args.num_scripts}份话术...")
                
                if args.async_generation:
                    # 异步生成话术（后台执行）
                    if generate_scripts_async(transcript_file, scripts_output_file, args.num_scripts, output_dir):
                        print(f"✅ 已启动{args.num_scripts}份话术的后台生成任务")
                        processed_count += 1
                    else:
                        print(f"❌ 启动后台生成话术任务失败")
                else:
                    # 同步生成话术
                    if generate_multiple_scripts(transcript_file, scripts_output_file, args.num_scripts):
                        print(f"✅ {args.num_scripts}份话术生成完成: {scripts_output_file}")
                        processed_count += 1
                    else:
                        print(f"❌ 多份话术生成失败")
            else:
                print(f"❌ 找不到转写文件: {transcript_file}")
        else:
            print(f"❌ 文件 {wav_file} 处理失败")
    
    print("\n所有文件处理完成！")
    print(f"成功处理: {processed_count}/{len(wav_files)} 个文件")
    print(f"输出结果保存在 {output_base_dir} 目录下")

if __name__ == "__main__":
    main()
