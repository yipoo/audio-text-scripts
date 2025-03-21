"""
直播升级营销项目主程序
"""
import os
import argparse
import json
from datetime import datetime
import sys

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 导入项目根目录的配置
try:
    from config import OUTPUT_DIR, UPLOADS_DIR
except ImportError:
    # 如果导入失败，使用默认值
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
    UPLOADS_DIR = os.path.join(ROOT_DIR, "uploads")
    
    # 确保目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)

# 检查是否在虚拟环境中运行
def check_virtual_env():
    """检查是否在虚拟环境中运行"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return True
    return False

# 如果不在虚拟环境中，给出提示
if not check_virtual_env():
    print("警告: 当前未在虚拟环境中运行。建议使用虚拟环境以避免依赖冲突。")
    print("您可以通过以下命令激活虚拟环境:")
    print("  source venv/bin/activate 或 ./activate_env.sh")
    print("如果您尚未创建虚拟环境，请先运行:")
    print("  ./setup_env.sh")
    
    # 询问是否继续
    response = input("是否仍要继续? (y/n): ")
    if response.lower() != 'y':
        sys.exit(0)

# 导入项目模块
try:
    from utils.config import check_config
    from audio_processing.recorder import AudioRecorder
    from audio_processing.speech_to_text import SpeechToText
    from text_processing.segmenter import TextSegmenter
    from text_processing.tagger import TextTagger
    from ai_generation.content_creator import ContentCreator
except ImportError as e:
    print(f"导入模块失败: {str(e)}")
    print("请确保已安装所有依赖: pip install -r requirements.txt")
    sys.exit(1)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="直播升级营销工具")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 录制命令
    record_parser = subparsers.add_parser("record", help="录制抖音直播语音")
    record_parser.add_argument("--duration", type=int, help="录制时长（秒），不指定则手动停止")
    record_parser.add_argument("--output", help="输出文件路径")
    
    # 转写命令
    transcribe_parser = subparsers.add_parser("transcribe", help="语音转文字")
    transcribe_parser.add_argument("--input", required=True, help="输入音频文件路径")
    transcribe_parser.add_argument("--output", help="输出文件路径")
    
    # 分段命令
    segment_parser = subparsers.add_parser("segment", help="文本分段处理")
    segment_parser.add_argument("--input", required=True, help="输入文本文件路径")
    segment_parser.add_argument("--output", help="输出文件路径")
    
    # 创作命令
    create_parser = subparsers.add_parser("create", help="AI内容创作")
    create_parser.add_argument("--input", required=True, help="输入分段文件路径")
    create_parser.add_argument("--output", help="输出文件路径")
    
    # 一键处理命令
    process_parser = subparsers.add_parser("process", help="一键处理（录制->转写->分段->创作）")
    process_parser.add_argument("--duration", type=int, help="录制时长（秒），不指定则手动停止")
    process_parser.add_argument("--output-dir", help="输出目录")
    
    # 从文件处理命令
    process_file_parser = subparsers.add_parser("process-file", help="从音频文件处理（转写->分段->创作）")
    process_file_parser.add_argument("--input", required=True, help="输入音频文件路径")
    process_file_parser.add_argument("--output-dir", help="输出目录")
    
    return parser.parse_args()

def record_audio(args):
    """录制音频"""
    recorder = AudioRecorder()
    audio_file = recorder.record_from_douyin(args.duration, args.output)
    print(f"录音已保存到: {audio_file}")
    return audio_file

def transcribe_audio(args):
    """转写音频"""
    stt = SpeechToText()
    text, output_file = stt.transcribe_file(args.input, args.output)
    print(f"转写结果已保存到: {output_file}")
    return text, output_file

def segment_text(args):
    """分段处理文本"""
    # 读取文本文件
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()
    
    segmenter = TextSegmenter()
    segments, output_file = segmenter.process_text(text, args.output)
    print(f"分段结果已保存到: {output_file}")
    return segments, output_file

def create_content(args):
    """AI内容创作"""
    # 读取分段文件
    with open(args.input, 'r', encoding='utf-8') as f:
        segments = json.load(f)
    
    creator = ContentCreator()
    results, output_file = creator.process_segments(segments, args.output)
    print(f"创作结果已保存到: {output_file}")
    return results, output_file

def process_all(args):
    """一键处理（录制->转写->分段->创作）"""
    # 创建输出目录
    output_dir = args.output_dir
    if output_dir is None:
        # 使用配置文件中的输出目录
        output_dir = OUTPUT_DIR
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(output_dir, f"job_{timestamp}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 录制音频
    recorder = AudioRecorder(output_dir=output_dir)
    audio_file = recorder.record_from_douyin(args.duration)
    
    # 转写音频
    stt = SpeechToText()
    text, text_file = stt.transcribe_file(audio_file, os.path.join(output_dir, "transcript.txt"))
    
    # 检查转写结果是否有内容
    if not text or text.strip() == "":
        print(f"\n警告：转写结果为空，无法进行后续处理")
        print(f"转写文件: {text_file}")
        return None, None
    
    # 分段处理
    segmenter = TextSegmenter()
    segments, segment_file = segmenter.process_text(text, os.path.join(output_dir, "segments.json"))
    
    # 检查分段结果是否有内容
    if not segments or len(segments) == 0:
        print(f"\n警告：分段结果为空，无法进行内容创作")
        print(f"转写文件: {text_file}")
        print(f"分段文件: {segment_file}")
        return segments, segment_file
    
    # AI创作
    creator = ContentCreator()
    results, result_file = creator.process_segments(segments, os.path.join(output_dir, "generated.json"))
    
    print(f"\n处理完成！所有输出文件已保存到: {output_dir}")
    print(f"音频文件: {audio_file}")
    print(f"转写文件: {text_file}")
    print(f"分段文件: {segment_file}")
    print(f"创作文件: {result_file}")
    
    return results, result_file

def process_from_file(args):
    """处理音频文件（语音转文字、分段、创作）"""
    print(f"处理文件: {args.input}")
    print(f"输出目录: {args.output_dir}")
    
    try:
        # 确保输出目录存在
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        
        # 1. 语音转文字
        transcriber = SpeechToText()
        transcript_file = os.path.join(args.output_dir, "transcript.txt")
        transcript = transcriber.transcribe_file(args.input, transcript_file)
        
        if not transcript:
            print("处理失败: 语音转写结果为空")
            return False
        
        print(f"🔊 语音转写完成，共 {len(transcript)} 字符")
        
        # 2. 文本分段
        print(f"📋 开始文本分段...")
        segmenter = TextSegmenter()
        segments, segments_file = segmenter.process_text(transcript, os.path.join(args.output_dir, "segments.json"))
        
        print(f"分段结果已保存到: {segments_file}")
        print(f"📋 文本分段完成，共 {len(segments)} 个段落")
        
        # 3. 内容创作
        print(f"🤖 开始内容创作...")
        creator = ContentCreator()
        results, output_file = creator.process_segments(segments, os.path.join(args.output_dir, "generated.json"))
        
        print(f"创作结果已保存到: {output_file}")
        print(f"🤖 内容创作完成，共生成 {len(results)} 个内容")
        
        return True
        
    except Exception as e:
        print(f"处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="直播升级营销工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 处理文件子命令
    process_parser = subparsers.add_parser("process-file", help="处理音频文件")
    process_parser.add_argument("--input", "-i", required=True, help="输入音频文件路径")
    process_parser.add_argument("--output-dir", "-o", help="输出目录")
    
    # 分段子命令
    segment_parser = subparsers.add_parser("segment", help="对文本进行分段")
    segment_parser.add_argument("--input", "-i", required=True, help="输入文本文件路径")
    segment_parser.add_argument("--output", "-o", required=True, help="输出分段JSON文件路径")
    
    # 创作子命令
    create_parser = subparsers.add_parser("create", help="根据分段生成内容")
    create_parser.add_argument("--input", "-i", required=True, help="输入分段JSON文件路径")
    create_parser.add_argument("--output", "-o", required=True, help="输出创作JSON文件路径")
    
    # 解析参数
    args = parser.parse_args()
    
    # 根据子命令执行相应的功能
    if args.command == "process-file":
        # 如果没有指定输出目录，则使用默认目录
        if not args.output_dir:
            # 获取文件名（不含扩展名）
            filename = os.path.basename(args.input)
            filename = os.path.splitext(filename)[0]
            # 创建输出目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.output_dir = os.path.join("output", f"{filename}_{timestamp}")
        
        # 确保输出目录存在
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 处理文件
        success = process_from_file(args)
        if not success:
            sys.exit(1)
    
    elif args.command == "segment":
        # 分段处理
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()
        
        segmenter = TextSegmenter()
        segments = segmenter.segment(text)
        
        # 保存分段结果
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        
        print(f"分段结果已保存到: {args.output}")
    
    elif args.command == "create":
        # 内容创作
        with open(args.input, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        
        creator = ContentCreator()
        results = creator.process_segments(segments)
        
        # 保存创作结果
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"创作结果已保存到: {args.output}")
    
    elif args.command == "record":
        record_audio(args)
    elif args.command == "transcribe":
        transcribe_audio(args)
    elif args.command == "process":
        process_all(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
