"""
音频录制模块
"""
import os
import time
import wave
import numpy as np
from datetime import datetime

# 尝试导入PyAudio，如果失败则使用sounddevice作为替代
try:
    import pyaudio
    USE_PYAUDIO = True
except ImportError:
    import sounddevice as sd
    import soundfile as sf
    USE_PYAUDIO = False

class AudioRecorder:
    """录音机类，用于录制音频"""
    
    def __init__(self, output_dir="recordings", format=None, channels=1, 
                 rate=16000, chunk=1024, threshold=0.03, silence_timeout=2):
        """
        初始化录音机
        
        Args:
            output_dir: 录音文件输出目录
            format: 音频格式 (仅PyAudio使用)
            channels: 通道数
            rate: 采样率
            chunk: 缓冲区大小
            threshold: 声音检测阈值
            silence_timeout: 静音超时时间（秒）
        """
        self.format = format if format is not None else (pyaudio.paInt16 if USE_PYAUDIO else None)
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.threshold = threshold
        self.silence_timeout = silence_timeout
        self.output_dir = output_dir
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def record(self, duration=None, filename=None):
        """
        录制音频
        
        Args:
            duration: 录制时长（秒），None表示手动停止
            filename: 输出文件名，None表示自动生成
            
        Returns:
            录音文件路径
        """
        if filename is None:
            # 生成文件名：recordings/record_YYYYMMDD_HHMMSS.wav
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"record_{timestamp}.wav")
        
        if USE_PYAUDIO:
            return self._record_with_pyaudio(duration, filename)
        else:
            return self._record_with_sounddevice(duration, filename)
    
    def _record_with_pyaudio(self, duration, filename):
        """使用PyAudio录制音频"""
        # 初始化PyAudio
        audio = pyaudio.PyAudio()
        
        # 打开音频流
        stream = audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        print(f"* 开始录音... {'按Ctrl+C停止' if duration is None else f'将在{duration}秒后自动停止'}")
        
        frames = []
        start_time = time.time()
        silence_start = None
        
        try:
            # 录制循环
            while True:
                # 检查是否达到指定时长
                if duration is not None and time.time() - start_time >= duration:
                    break
                
                # 读取音频数据
                data = stream.read(self.chunk)
                frames.append(data)
                
                # 计算音量
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume_norm = np.abs(audio_data).mean() / 32767.0
                
                # 检测静音
                if volume_norm < self.threshold:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > self.silence_timeout:
                        print("检测到静音，录音停止")
                        break
                else:
                    silence_start = None
                
        except KeyboardInterrupt:
            print("* 录音手动停止")
        finally:
            # 停止并关闭音频流
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # 保存录音文件
            self._save_recording(frames, filename)
            
            print(f"* 录音已保存到: {filename}")
            return filename
    
    def _record_with_sounddevice(self, duration, filename):
        """使用sounddevice录制音频"""
        print(f"* 开始录音... {'按Ctrl+C停止' if duration is None else f'将在{duration}秒后自动停止'}")
        
        # 计算总帧数
        if duration is not None:
            total_frames = int(self.rate * duration)
        else:
            # 设置一个较大的值，实际会在KeyboardInterrupt时停止
            total_frames = int(self.rate * 3600)  # 最多录制1小时
        
        try:
            # 录制音频
            recording = sd.rec(
                total_frames,
                samplerate=self.rate,
                channels=self.channels,
                dtype='int16'
            )
            
            # 如果是无限录制，等待用户中断
            if duration is None:
                print("按Ctrl+C停止录音...")
                sd.wait()
            else:
                # 否则等待指定时长
                sd.wait()
                
        except KeyboardInterrupt:
            print("* 录音手动停止")
            sd.stop()
        
        # 保存录音文件
        sf.write(filename, recording, self.rate)
        print(f"* 录音已保存到: {filename}")
        return filename
    
    def _save_recording(self, frames, filename):
        """保存录音到文件 (PyAudio方式)"""
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
    
    def process_audio(self, input_file, output_file=None, normalize=True):
        """
        处理音频文件（使用soundfile和numpy替代pydub）
        
        Args:
            input_file: 输入音频文件路径
            output_file: 输出音频文件路径，None表示自动生成
            normalize: 是否进行音量标准化
            
        Returns:
            处理后的音频文件路径
        """
        # 如果未指定输出文件，则自动生成
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_dir = os.path.dirname(input_file)
            output_file = os.path.join(output_dir, f"{base_name}_processed.wav")
        
        try:
            # 读取音频文件
            data, samplerate = sf.read(input_file)
            
            # 标准化音量
            if normalize and len(data) > 0:
                # 计算归一化因子
                max_val = np.max(np.abs(data))
                if max_val > 0:
                    # 归一化到0.9以避免削波
                    data = data * (0.9 / max_val)
            
            # 保存处理后的音频
            sf.write(output_file, data, samplerate)
            
            print(f"音频处理完成: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"音频处理失败: {str(e)}")
            return input_file
        
    def record_from_douyin(self, duration=None, filename=None):
        """
        从抖音直播录制音频
        注意：此方法需要用户手动将抖音直播的声音输出到系统麦克风输入
        
        Args:
            duration: 录制时长（秒），None表示手动停止
            filename: 输出文件名，None表示自动生成
            
        Returns:
            录音文件路径
        """
        print("请确保抖音直播声音已经输出到系统...")
        return self.record(duration, filename)
