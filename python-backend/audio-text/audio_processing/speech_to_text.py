"""
语音转文字模块 - 使用阿里云语音识别服务
"""
import os
import json
import time
import logging
import wave
import tempfile
import subprocess
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('speech_to_text')

# 尝试导入阿里云NLS SDK
try:
    import nls
    from nls.token import getToken
    USE_SDK = True
    logger.info("成功导入阿里云NLS SDK")
except ImportError as e:
    USE_SDK = False
    logger.error(f"阿里云NLS SDK导入失败: {str(e)}")
    logger.error("请确保已安装阿里云NLS SDK: 请参考阿里云文档安装SDK")

from utils.config import (
    ALIYUN_ACCESS_KEY_ID,
    ALIYUN_ACCESS_KEY_SECRET,
    ALIYUN_APPKEY,
    ALIYUN_REGION
)

def get_audio_info(audio_file):
    """
    获取音频文件信息
    
    Args:
        audio_file: 音频文件路径
        
    Returns:
        (采样率, 声道数, 位深度)
    """
    try:
        with wave.open(audio_file, 'rb') as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth() * 8  # 转换为位深度
            
            logger.info(f"音频信息 - 采样率: {sample_rate}Hz, 声道数: {channels}, 位深度: {sample_width}bit")
            return sample_rate, channels, sample_width
    except Exception as e:
        logger.error(f"获取音频信息失败: {str(e)}")
        return None, None, None

def convert_audio(audio_file, target_sample_rate=16000, target_channels=1):
    """
    转换音频文件采样率和声道数
    
    Args:
        audio_file: 原始音频文件路径
        target_sample_rate: 目标采样率，默认16000Hz
        target_channels: 目标声道数，默认1（单声道）
        
    Returns:
        转换后的临时文件路径
    """
    try:
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_file.close()
        
        # 使用ffmpeg转换音频
        cmd = [
            'ffmpeg', 
            '-i', audio_file, 
            '-ar', str(target_sample_rate), 
            '-ac', str(target_channels),
            '-y',  # 覆盖输出文件
            temp_file.name
        ]
        
        logger.info(f"转换音频文件: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"音频转换失败: {result.stderr}")
            return None
        
        logger.info(f"音频转换成功，临时文件: {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        logger.error(f"音频转换出错: {str(e)}")
        return None

class SpeechToText:
    """语音转文字类，使用阿里云语音识别服务"""
    
    def __init__(self, format_type="wav", sample_rate=16000, enable_punctuation=True, enable_inverse_text_normalization=True):
        """
        初始化语音转文字对象
        
        Args:
            format_type: 音频格式，默认为wav
            sample_rate: 采样率，默认为16000
            enable_punctuation: 是否启用标点符号，默认为True
            enable_inverse_text_normalization: 是否启用文本反规范化，默认为True
        """
        self.format_type = format_type
        self.sample_rate = sample_rate
        self.enable_punctuation = enable_punctuation
        self.enable_inverse_text_normalization = enable_inverse_text_normalization
        
        # 初始化状态变量
        self.all_results = []
        self.current_sentence = ""
        self.is_finished = False
        self.transcript = ""
        self.output_file = None
        self.processed_sentences = set()  # 用于跟踪已处理的句子，避免重复
        
        logger.info(f"初始化语音转文字对象，格式: {format_type}, 采样率: {sample_rate}")
        
        # 安全地打印API密钥信息
        if ALIYUN_ACCESS_KEY_ID:
            logger.info(f"ALIYUN_ACCESS_KEY_ID: {ALIYUN_ACCESS_KEY_ID[:3]}...{ALIYUN_ACCESS_KEY_ID[-3:]}")
        else:
            logger.info("ALIYUN_ACCESS_KEY_ID: None")
            
        if ALIYUN_ACCESS_KEY_SECRET:
            logger.info(f"ALIYUN_ACCESS_KEY_SECRET: {ALIYUN_ACCESS_KEY_SECRET[:3]}...{ALIYUN_ACCESS_KEY_SECRET[-3:]}")
        else:
            logger.info("ALIYUN_ACCESS_KEY_SECRET: None")
            
        logger.info(f"ALIYUN_APPKEY: {ALIYUN_APPKEY}")
        logger.info(f"ALIYUN_REGION: {ALIYUN_REGION}")
        
        # 检查API密钥是否配置
        if not ALIYUN_ACCESS_KEY_ID or not ALIYUN_ACCESS_KEY_SECRET or not ALIYUN_APPKEY:
            logger.error("API密钥未正确配置，请检查.env文件")
            raise ValueError("API密钥未正确配置，请检查.env文件")
            
        if not USE_SDK:
            logger.error("阿里云NLS SDK不可用，请安装SDK")
            raise ImportError("阿里云NLS SDK不可用，请安装SDK")
    
    def transcribe(self, audio_file):
        """
        转写音频文件
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            转写结果
        """
        if not os.path.exists(audio_file):
            logger.error(f"音频文件不存在: {audio_file}")
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        logger.info(f"开始转写音频文件: {audio_file}")
        
        # 获取音频信息
        sample_rate, channels, _ = get_audio_info(audio_file)
        
        # 检查采样率和声道数是否需要转换
        converted_file = None
        if sample_rate != 16000 or channels != 1:
            logger.info(f"音频需要转换: 采样率 {sample_rate}Hz -> 16000Hz, 声道数 {channels} -> 1")
            converted_file = convert_audio(audio_file, 16000, 1)
            if converted_file:
                logger.info(f"使用转换后的音频文件: {converted_file}")
                audio_file = converted_file
                self.sample_rate = 16000
            else:
                logger.warning("音频转换失败，尝试使用原始文件")
        
        try:
            # 转写音频
            result = self._transcribe_with_sdk(audio_file)
            
            # 如果使用了临时文件，删除它
            if converted_file and os.path.exists(converted_file):
                os.unlink(converted_file)
                logger.info(f"已删除临时文件: {converted_file}")
                
            return result
            
        except Exception as e:
            # 如果出错，也要删除临时文件
            if converted_file and os.path.exists(converted_file):
                os.unlink(converted_file)
                logger.info(f"已删除临时文件: {converted_file}")
            raise
    
    def transcribe_file(self, audio_file, output_file=None):
        """
        转写音频文件并保存结果到文本文件
        
        Args:
            audio_file: 音频文件路径
            output_file: 输出文件路径，None表示不保存
            
        Returns:
            (转写结果, 输出文件路径)
        """
        # 保存输出文件路径，用于实时写入
        self.output_file = output_file
        
        # 如果指定了输出文件，确保输出目录存在
        if output_file:
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 创建空文件，准备实时写入
            with open(output_file, 'w', encoding='utf-8') as f:
                pass
            
        # 转写音频
        transcript = self.transcribe(audio_file)
        
        # 如果指定了输出文件，确保最终结果完整写入
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            logger.info(f"转写结果已保存到: {output_file}")
        
        return transcript, output_file
    
    def _transcribe_with_sdk(self, audio_file):
        """使用阿里云SDK进行语音识别"""
        logger.info("使用阿里云NLS SDK进行语音识别")
        
        try:
            # 获取Token
            token = getToken(ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET)
            if not token:
                raise Exception("获取Token失败")
            
            logger.info(f"成功获取Token: {token[:10]}...")
            
            # 重置状态
            self.all_results = []
            self.current_sentence = ""
            self.is_finished = False
            self.transcript = ""
            self.processed_sentences = set()  # 重置已处理句子集合
            
            # 创建识别请求
            logger.info("设置识别参数")
            sr = nls.NlsSpeechTranscriber(
                url=f"wss://nls-gateway.{ALIYUN_REGION}.aliyuncs.com/ws/v1",
                token=token,
                appkey=ALIYUN_APPKEY,
                on_start=None,
                on_sentence_begin=self._on_sentence_begin,
                on_sentence_end=self._on_sentence_end,
                on_result_changed=None,
                on_completed=self._on_completed,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # 开始识别，在start方法中设置参数
            logger.info("开始识别...")
            sr.start(
                aformat=self.format_type,
                sample_rate=self.sample_rate,
                enable_punctuation_prediction=self.enable_punctuation,
                enable_inverse_text_normalization=self.enable_inverse_text_normalization
            )
            
            # 读取音频文件并发送
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            # 分块发送音频数据
            chunk_size = 4096
            total_size = len(audio_data)
            sent_size = 0
            
            # 输出到控制台的进度条
            print(f"\r🔊 音频转写进度: 0%", end="", flush=True)
            
            for i in range(0, total_size, chunk_size):
                chunk = audio_data[i:i+chunk_size]
                sr.send_audio(chunk)
                
                # 更新发送进度
                sent_size += len(chunk)
                progress = sent_size / total_size * 100
                
                # 每10%更新一次进度条
                if int(progress) % 10 == 0 and int(progress) > 0:
                    print(f"\r🔊 音频转写进度: {int(progress)}%", end="", flush=True)
                
                # 记录发送进度到日志
                if i % (chunk_size * 10) == 0 or i + chunk_size >= total_size:
                    logger.info(f"已发送 {sent_size}/{total_size} 字节 ({progress:.1f}%)")
            
            # 完成进度条
            print(f"\r🔊 音频转写进度: 100% ✅", flush=True)
            
            # 停止发送音频
            sr.stop()
            
            # 等待识别完成
            while not self.is_finished:
                time.sleep(0.1)
            
            # 返回转写结果
            return self.transcript
            
        except Exception as e:
            logger.error(f"语音识别失败: {str(e)}")
            raise
    
    def _on_sentence_begin(self, message, *args, **kwargs):
        """句子开始回调"""
        try:
            logger.info(f"句子开始: {message}")
            # 检查message是否是字符串，如果是，尝试解析为JSON
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    logger.error(f"无法解析句子开始事件消息: {message}")
                    return
                    
            # 检查message是否是字典
            if not isinstance(message, dict):
                logger.error(f"句子开始事件消息不是字典: {type(message)}")
                return
                
            # 检查payload是否存在
            if "payload" not in message:
                logger.error(f"句子开始事件中缺少payload数据: {message}")
                return
                
            # 获取句子ID和时间
            sentence_id = message["payload"].get("index", 0)
            sentence_time = message["payload"].get("time", 0)
            
            progress_info = f"音频转写进度: 开始转写第 {sentence_id} 句，时间点: {sentence_time}ms"
            print(progress_info, flush=True)
        except Exception as e:
            logger.error(f"处理句子开始事件出错: {str(e)}")
    
    def _on_sentence_end(self, message, *args, **kwargs):
        """句子结束回调"""
        try:
            logger.info(f"句子结束: {message}")
            
            # 检查message是否是字符串，如果是，尝试解析为JSON
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    logger.error(f"无法解析句子结束事件消息: {message}")
                    return
            
            # 检查message是否是字典
            if not isinstance(message, dict):
                logger.error(f"句子结束事件消息不是字典: {type(message)}")
                return
                
            # 检查payload是否存在且不为None
            if "payload" not in message or message["payload"] is None:
                logger.error(f"句子结束事件中缺少payload数据: {message}")
                return
                
            # 获取结果
            result = message["payload"].get("result", "")
            sentence_id = message["payload"].get("sentence_id", "")
            
            # 如果这个句子已经处理过，跳过
            if sentence_id and sentence_id in self.processed_sentences:
                logger.info(f"句子 {sentence_id} 已处理过，跳过")
                return
                
            # 添加到已处理集合
            if sentence_id:
                self.processed_sentences.add(sentence_id)
                
            # 添加到结果列表
            if result:
                self.all_results.append(result)
                
                # 更新当前完整转写文本
                self.transcript = " ".join(self.all_results)
                
                # 如果指定了输出文件，实时写入
                if self.output_file:
                    with open(self.output_file, 'w', encoding='utf-8') as f:
                        f.write(self.transcript)
                        
                logger.info(f"当前转写结果: {self.transcript}")
        except Exception as e:
            logger.error(f"处理句子结束事件出错: {str(e)}")
    
    def _on_completed(self, message, *args, **kwargs):
        """转写完成回调"""
        try:
            logger.info(f"识别完成: {message}")
            
            # 检查message是否是字符串，如果是，尝试解析为JSON
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    logger.warning(f"识别完成事件收到无效消息: {message}")
                    return
            
            # 检查message是否是字典
            if not isinstance(message, dict):
                logger.warning(f"识别完成事件消息不是字典: {type(message)}")
                return
            
            # 如果转写结果为空，尝试使用之前收集的句子
            if not self.transcript and self.all_results:
                self.transcript = " ".join(self.all_results)
                
            # 如果指定了输出文件，确保最终结果被写入
            if self.output_file and self.transcript:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write(self.transcript)
                logger.info(f"转写结果已保存到: {self.output_file}")
            
            # 标记转写完成
            self.is_finished = True
            
        except Exception as e:
            logger.error(f"处理转写完成事件出错: {str(e)}")
    
    def _on_error(self, message, *args, **kwargs):
        """错误回调"""
        try:
            logger.error(f"识别错误: {message}")
            self.is_finished = True
        except Exception as e:
            logger.error(f"处理错误事件出错: {str(e)}")
    
    def _on_close(self, *args, **kwargs):
        """连接关闭回调"""
        try:
            logger.info("连接关闭")
            self.is_finished = True
        except Exception as e:
            logger.error(f"处理连接关闭事件出错: {str(e)}")
    
    def process_directory(self, input_dir, output_dir=None):
        """
        处理目录中的所有音频文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录，None表示自动生成
            
        Returns:
            (处理结果, 输出目录)
        """
        # 确保输入目录存在
        if not os.path.exists(input_dir):
            logger.error(f"输入目录不存在: {input_dir}")
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        # 如果没有指定输出目录，自动生成
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"transcripts_{timestamp}"
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        logger.info(f"处理目录: {input_dir}")
        logger.info(f"输出目录: {output_dir}")
        
        # 获取所有音频文件
        audio_files = []
        for file in os.listdir(input_dir):
            if file.endswith(f".{self.format_type}"):
                audio_files.append(os.path.join(input_dir, file))
        
        logger.info(f"找到{len(audio_files)}个音频文件")
        
        # 处理每个音频文件
        results = {}
        for audio_file in audio_files:
            try:
                logger.info(f"处理文件: {audio_file}")
                
                # 生成输出文件名
                base_name = os.path.basename(audio_file)
                output_name = os.path.splitext(base_name)[0] + ".txt"
                output_file = os.path.join(output_dir, output_name)
                
                # 转写音频并保存结果
                transcript, saved_file = self.transcribe_file(audio_file, output_file)
                
                # 添加到结果
                results[audio_file] = {
                    "transcript": transcript,
                    "output_file": saved_file
                }
                
            except Exception as e:
                logger.error(f"处理文件出错: {audio_file}, 错误: {str(e)}")
                results[audio_file] = {
                    "error": str(e)
                }
        
        logger.info(f"处理完成，共处理{len(results)}个文件")
        return results, output_dir
