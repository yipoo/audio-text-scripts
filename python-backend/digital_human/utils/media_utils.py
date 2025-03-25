import cv2
import numpy as np
import torch
import torchaudio
from pathlib import Path
import tempfile
import os
import subprocess

from digital_human.config.config import AUDIO_CONFIG, VIDEO_CONFIG

class MediaUtils:
    @staticmethod
    def load_audio(file_path, target_sr=None):
        """
        加载音频文件
        
        Args:
            file_path (str): 音频文件路径
            target_sr (int, optional): 目标采样率
            
        Returns:
            tuple: (音频数据, 采样率)
        """
        waveform, sample_rate = torchaudio.load(file_path)
        if target_sr is not None and target_sr != sample_rate:
            waveform = torchaudio.functional.resample(waveform, sample_rate, target_sr)
            sample_rate = target_sr
        return waveform, sample_rate

    @staticmethod
    def save_audio(waveform, sample_rate, file_path):
        """
        保存音频文件
        
        Args:
            waveform (torch.Tensor): 音频数据
            sample_rate (int): 采样率
            file_path (str): 保存路径
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(file_path, waveform, sample_rate)

    @staticmethod
    def load_video(file_path):
        """
        加载视频文件
        
        Args:
            file_path (str): 视频文件路径
            
        Returns:
            tuple: (帧列表, 帧率)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"视频文件不存在: {file_path}")
        
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {file_path}")
        
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # 将BGR转换为RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        return frames, fps

    @staticmethod
    def save_video(frames, fps, file_path, with_audio=None):
        """保存视频，保持原始颜色空间"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 创建临时文件
            temp_video = file_path + '.temp.mp4'
            
            # 使用更高质量的编码参数
            writer = cv2.VideoWriter(
                temp_video,
                cv2.VideoWriter_fourcc(*'mp4v'),
                fps,
                (frames[0].shape[1], frames[0].shape[0]),
                isColor=True
            )
            
            for frame in frames:
                # 确保颜色空间正确
                if len(frame.shape) == 2:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                elif frame.shape[2] == 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                writer.write(frame)
                
            writer.release()
            
            # 使用 ffmpeg 进行高质量转换
            if with_audio:
                cmd = [
                    'ffmpeg', '-y',
                    '-i', temp_video,
                    '-i', with_audio,
                    '-c:v', 'libx264',
                    '-preset', 'slow',  # 更慢但质量更好
                    '-crf', '18',       # 更低的值意味着更高的质量
                    '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    file_path
                ]
            else:
                cmd = [
                    'ffmpeg', '-y',
                    '-i', temp_video,
                    '-c:v', 'libx264',
                    '-preset', 'slow',
                    '-crf', '18',
                    '-pix_fmt', 'yuv420p',
                    file_path
                ]
            
            subprocess.run(cmd, check=True)
            
            # 清理临时文件
            if os.path.exists(temp_video):
                os.remove(temp_video)
                
        except Exception as e:
            print(f"保存视频时出错: {str(e)}")
            raise

    @staticmethod
    def extract_audio(video_path, output_path=None):
        """
        从视频中提取音频
        
        Args:
            video_path (str): 视频文件路径
            output_path (str, optional): 音频输出路径
            
        Returns:
            str: 音频文件路径
        """
        if output_path is None:
            output_path = str(Path(video_path).with_suffix('.wav'))
        
        # 使用FFmpeg提取音频
        os.system(f'ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 44100 -ac 2 {output_path} -y')
        
        return output_path

    @staticmethod
    def resize_video(frames, target_size):
        """
        调整视频尺寸
        
        Args:
            frames (list): 帧列表
            target_size (tuple): 目标尺寸 (width, height)
            
        Returns:
            list: 调整后的帧列表
        """
        if not frames:
            return frames
            
        target_width, target_height = target_size
        resized_frames = []
        
        for frame in frames:
            resized_frame = cv2.resize(frame, (target_width, target_height))
            resized_frames.append(resized_frame)
            
        return resized_frames

    @staticmethod
    def normalize_audio(waveform):
        """
        归一化音频数据
        
        Args:
            waveform (torch.Tensor): 音频数据
            
        Returns:
            torch.Tensor: 归一化后的音频数据
        """
        if torch.is_tensor(waveform):
            max_val = torch.abs(waveform).max()
            if max_val > 0:
                return waveform / max_val
            return waveform
        else:
            max_val = np.abs(waveform).max()
            if max_val > 0:
                return waveform / max_val
            return waveform 