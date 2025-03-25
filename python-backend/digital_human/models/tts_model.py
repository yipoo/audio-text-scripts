import torch
import numpy as np
from pathlib import Path
import time
import os
import re
from typing import Optional, Tuple
import soundfile as sf
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
import librosa

from digital_human.config.config import MODEL_CONFIG, AUDIO_CONFIG, CACHE_DIR

class TextToSpeechModel:
    def __init__(self):
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        self.processor = None
        self.model = None
        self.vocoder = None
        self._load_models()

    def _load_models(self):
        print("正在加载TTS模型...")
        try:
            model_config = MODEL_CONFIG["text_to_speech"]
            model_name = model_config["model_name"]
            cache_dir = model_config["cache_dir"]
            self.language = model_config.get("language", "zh")

            # 加载处理器
            self.processor = SpeechT5Processor.from_pretrained(
                model_name,
                cache_dir=cache_dir
            )
            
            # 加载TTS模型
            self.model = SpeechT5ForTextToSpeech.from_pretrained(
                model_name,
                cache_dir=cache_dir
            ).to(self.device)
            
            # 加载vocoder
            self.vocoder = SpeechT5HifiGan.from_pretrained(
                "microsoft/speecht5_hifigan",
                cache_dir=cache_dir
            ).to(self.device)
            
            print("TTS模型加载完成")
        except Exception as e:
            print(f"加载TTS模型失败: {str(e)}")
            raise

    def _preprocess_chinese_text(self, text: str) -> str:
        """预处理中文文本"""
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 添加基本的标点符号规范化
        text = re.sub(r'[，,]', '，', text)
        text = re.sub(r'[。.]', '。', text)
        text = re.sub(r'[！!]', '！', text)
        text = re.sub(r'[？?]', '？', text)
        text = re.sub(r'[：:]', '：', text)
        text = re.sub(r'[；;]', '；', text)
        
        # 确保句子以标点符号结尾
        if not text[-1] in '。！？：；':
            text += '。'
            
        return text

    def generate_speech(self, text: str, output_path: Optional[str] = None, 
                       speaker: str = "default", speed: float = 1.0) -> Tuple[np.ndarray, int]:
        """
        生成语音
        Args:
            text (str): 要转换的文本
            output_path (str, optional): 输出文件路径
            speaker (str, optional): 说话人ID，目前只支持"default"
            speed (float, optional): 语速，范围0.5-2.0
        Returns:
            tuple: (音频数据, 采样率)
        """
        if not text:
            raise ValueError("文本不能为空")

        try:
            # 预处理中文文本
            if self.language == "zh":
                text = self._preprocess_chinese_text(text)

            # 处理输入文本
            inputs = self.processor(
                text=text,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            # 创建 speaker embeddings (全零向量，使用默认说话人)
            speaker_embeddings = torch.zeros((1, 512)).to(self.device)
            
            # 生成语音
            speech = self.model.generate_speech(
                inputs["input_ids"],
                speaker_embeddings=speaker_embeddings,
                vocoder=self.vocoder
            )
            
            # 转换为numpy数组
            speech = speech.cpu().numpy()

            # 调整语速（通过重采样实现）
            if speed != 1.0:
                speech = librosa.effects.time_stretch(speech, rate=1/speed)

            # 如果指定了输出路径，保存音频文件
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                sf.write(output_path, speech, AUDIO_CONFIG["sample_rate"])

            return speech, AUDIO_CONFIG["sample_rate"]

        except Exception as e:
            print(f"生成语音失败: {str(e)}")
            raise

    def preload_models(self):
        """预热模型"""
        print("预热TTS模型...")
        try:
            # 生成一个简短的测试音频
            self.generate_speech("测试")
            print("TTS模型预热完成")
        except Exception as e:
            print(f"预热TTS模型失败: {str(e)}")
            raise

    @staticmethod
    def get_available_speakers():
        """获取可用的说话人列表"""
        # 目前只支持默认说话人
        return ["default"]

    def __call__(self, text, **kwargs):
        """便捷调用接口"""
        return self.generate_speech(text, **kwargs)

# 创建单例实例
tts_model = TextToSpeechModel() 