import cv2
import numpy as np
from pathlib import Path
import torch
import librosa
import dlib
import face_alignment
from torch import nn
import torch.nn.functional as F
from typing import List, Tuple, Optional

from digital_human.config.config import MODEL_CONFIG, VIDEO_CONFIG, DATA_DIR, MODELS_DIR
from .wav2lip import load_wav2lip_model
from .viseme import viseme_mapper

class Wav2LipPredictor:
    def __init__(self, checkpoint_path):
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        self.model = self.load_model(checkpoint_path)
        self.mel_step_size = 16
        self.fps = VIDEO_CONFIG["frame_rate"]
        
    def load_model(self, checkpoint_path):
        model = Wav2Lip()
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        model.load_state_dict(checkpoint['state_dict'])
        model = model.to(self.device)
        model.eval()
        return model

    def get_mel_chunks(self, audio_path):
        """从音频文件中提取梅尔频谱图特征"""
        wav = librosa.load(audio_path, sr=16000)[0]
        mel = librosa.feature.melspectrogram(y=wav, sr=16000, n_mels=80, 
                                           n_fft=800, hop_length=200)
        mel = np.log(mel + 1e-6)
        return mel

    def predict(self, face_frames, audio_path):
        """生成口型同步的视频帧"""
        mel = self.get_mel_chunks(audio_path)
        frame_h, frame_w = face_frames[0].shape[:2]
        
        # 处理每一帧
        result_frames = []
        for i, frame in enumerate(face_frames):
            mel_chunk = mel[:, i*self.mel_step_size:(i+1)*self.mel_step_size]
            if mel_chunk.shape[1] < self.mel_step_size:
                break
                
            mel_chunk = torch.FloatTensor(mel_chunk).unsqueeze(0).to(self.device)
            frame_tensor = self.prepare_frame(frame)
            
            with torch.no_grad():
                pred = self.model(mel_chunk, frame_tensor)
                pred = pred.cpu().numpy().transpose(0, 2, 3, 1)[0] * 255.
                pred = pred.astype(np.uint8)
                pred = cv2.resize(pred, (frame_w, frame_h))
                
            result_frames.append(pred)
            
        return result_frames

    def prepare_frame(self, frame):
        """预处理视频帧"""
        frame = cv2.resize(frame, (96, 96))
        frame_tensor = torch.FloatTensor(frame).permute(2, 0, 1).unsqueeze(0)
        frame_tensor = frame_tensor.to(self.device)
        return frame_tensor

class FaceAnimationModel:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.face_detector = None
        self.landmark_predictor = None
        self.face_aligner = None
        self.base_image = None
        self.base_landmarks = None
        self._load_models()

    def _load_models(self):
        """加载人脸检测和特征点检测模型"""
        print("正在加载人脸模型...")
        try:
            # 加载dlib的人脸检测器
            self.face_detector = dlib.get_frontal_face_detector()
            
            # 加载特征点检测模型
            predictor_path = MODELS_DIR / "shape_predictor_68_face_landmarks.dat"
            if not predictor_path.exists():
                raise FileNotFoundError(f"找不到特征点检测模型文件: {predictor_path}")
            self.landmark_predictor = dlib.shape_predictor(str(predictor_path))
            
            # 初始化face-alignment
            self.face_aligner = face_alignment.FaceAlignment(
                face_alignment.LandmarksType.TWO_D,
                device=self.device
            )
            
            print("人脸模型加载完成")
        except Exception as e:
            print(f"加载人脸模型失败: {str(e)}")
            raise

    def load_face_image(self, image_path: str):
        """加载基准人脸图像"""
        try:
            # 读取图像
            self.base_image = cv2.imread(image_path)
            if self.base_image is None:
                raise ValueError(f"无法读取图像: {image_path}")
            
            # 检测人脸
            faces = self.face_detector(self.base_image)
            if not faces:
                raise ValueError("未检测到人脸")
            
            # 获取第一个人脸的特征点
            face = faces[0]
            landmarks = self.landmark_predictor(self.base_image, face)
            self.base_landmarks = np.array([[p.x, p.y] for p in landmarks.parts()])
            
            # 提取嘴部区域的特征点（第49-68个点）
            self.mouth_points = self.base_landmarks[48:68]
            
            print("基准人脸图像加载完成")
        except Exception as e:
            print(f"加载人脸图像失败: {str(e)}")
            raise

    def _apply_landmarks_to_image(self, image: np.ndarray, 
                                  landmarks: np.ndarray) -> np.ndarray:
        """将嘴型关键点应用到图像上"""
        try:
            # 创建图像副本
            result = image.copy()
            
            # 确保 landmarks 是浮点数类型
            landmarks = landmarks.astype(np.float64)
            
            # 检查 mouth_points 是否存在
            if self.mouth_points is None or len(self.mouth_points) < 20:
                print("警告: 嘴部关键点不存在或不完整")
                return result
            
            # 检查 landmarks 的维度
            if landmarks.shape[0] < 8:
                print(f"警告: landmarks 维度不足，当前维度: {landmarks.shape}")
                # 创建足够大的 landmarks 数组
                extended_landmarks = np.zeros((8, 2), dtype=np.float64)
                extended_landmarks[:landmarks.shape[0]] = landmarks
                landmarks = extended_landmarks
            
            # 获取原始嘴部区域
            mouth_points_int = self.mouth_points.astype(np.int32)
            mouth_hull = cv2.convexHull(mouth_points_int)
            
            # 应用新的嘴型关键点
            new_mouth_points = self.mouth_points.copy().astype(np.float64)
            
            # 对上嘴唇应用变形
            for i in range(7):  # 嘴唇上部的7个点
                factor = 1.0 - 0.7 * abs(i - 3) / 3  # 中间点变形最大
                idx = min(i % 4, 3)  # 确保索引不超过3
                new_mouth_points[i] += landmarks[idx] * factor
            
            # 对下嘴唇应用变形
            for i in range(7):  # 嘴唇下部的7个点
                idx = i + 11  # 下嘴唇起始索引
                factor = 1.0 - 0.7 * abs(i - 3) / 3  # 中间点变形最大
                idx2 = min(4 + (i % 4), 7)  # 确保索引不超过7
                new_mouth_points[idx] += landmarks[idx2] * factor
            
            # 对内部轮廓点应用变形
            for i in range(12, 20):
                factor = 0.5  # 内轮廓变形程度较小
                if i < 16:  # 上内轮廓
                    idx = min(i - 12, 3)  # 确保索引不超过3
                    new_mouth_points[i] += landmarks[idx] * factor
                else:  # 下内轮廓
                    idx = min(4 + (i - 16), 7)  # 确保索引不超过7
                    new_mouth_points[i] += landmarks[idx] * factor
            
            # 转换为整数用于绘图
            new_mouth_points_int = new_mouth_points.astype(np.int32)
            
            # 创建新的嘴型区域掩码
            new_mouth_hull = cv2.convexHull(new_mouth_points_int)
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.fillConvexPoly(mask, new_mouth_hull, 255)
            
            # 创建一个只包含嘴部区域的图像
            mouth_only = np.zeros_like(result)
            
            # 直接从原始图像复制嘴唇区域
            for y in range(result.shape[0]):
                for x in range(result.shape[1]):
                    if cv2.pointPolygonTest(new_mouth_hull, (x, y), False) >= 0:
                        # 复制原始图像中的颜色
                        mouth_only[y, x] = result[y, x]
            
            # 计算嘴部中心点
            center = np.mean(new_mouth_points_int, axis=0).astype(np.int32)
            center_point = (int(center[0]), int(center[1]))
            
            # 使用无缝克隆将嘴部区域合成到结果图像中
            try:
                output = cv2.seamlessClone(
                    mouth_only, result, mask, 
                    center_point, 
                    cv2.NORMAL_CLONE
                )
                return output
            except Exception as e:
                print(f"无缝克隆失败: {e}")
                return result
        
        except Exception as e:
            print(f"应用嘴型关键点失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return image

    def generate_talking_video(self, audio_file: str, text: str) -> Tuple[List[np.ndarray], int]:
        """生成说话的视频序列"""
        try:
            if self.base_image is None:
                raise ValueError("请先加载基准人脸图像")
            
            # 获取音频时长
            audio_info = librosa.get_duration(filename=audio_file)
            duration = float(audio_info)
            
            # 生成嘴型关键点序列
            landmarks_seq = viseme_mapper.generate_landmarks_sequence(
                text, duration, VIDEO_CONFIG["frame_rate"]
            )
            
            # 生成视频帧
            frames = []
            for landmarks in landmarks_seq:
                frame = self._apply_landmarks_to_image(self.base_image, landmarks)
                frames.append(frame)
            
            return frames, VIDEO_CONFIG["frame_rate"]
            
        except Exception as e:
            print(f"生成说话视频失败: {str(e)}")
            raise

    def generate_idle_video(self, duration_seconds: float = 5.0) -> Tuple[List[np.ndarray], int]:
        """生成空闲状态的视频序列"""
        try:
            if self.base_image is None:
                raise ValueError("请先加载基准人脸图像")
            
            # 生成空闲状态的关键点序列
            total_frames = int(duration_seconds * VIDEO_CONFIG["frame_rate"])
            idle_landmarks = viseme_mapper.get_viseme_landmarks(0)  # 使用闭合嘴型
            
            # 生成视频帧
            frames = []
            for _ in range(total_frames):
                frame = self._apply_landmarks_to_image(self.base_image, idle_landmarks)
                frames.append(frame)
            
            return frames, VIDEO_CONFIG["frame_rate"]
            
        except Exception as e:
            print(f"生成空闲视频失败: {str(e)}")
            raise

class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):
        super(ConvBlock, self).__init__()
        self.conv_block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size, stride=stride, padding=padding),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.conv_block(x)

class Wav2Lip(nn.Module):
    def __init__(self):
        super(Wav2Lip, self).__init__()
        
        # 面部编码器块 - 匹配预训练权重的结构
        self.face_encoder_blocks = nn.ModuleList([
            nn.Sequential(
                ConvBlock(6, 16, kernel_size=7),
                ConvBlock(16, 16),
                ConvBlock(16, 16),
            ),
            nn.Sequential(
                ConvBlock(16, 32, stride=2),
                ConvBlock(32, 32),
                ConvBlock(32, 32),
            ),
            nn.Sequential(
                ConvBlock(32, 64, stride=2),
                ConvBlock(64, 64),
                ConvBlock(64, 64),
            ),
            nn.Sequential(
                ConvBlock(64, 128, stride=2),
                ConvBlock(128, 128),
                ConvBlock(128, 128),
            ),
        ])
        
        # 音频编码器 - 匹配预训练权重的结构
        self.audio_encoder = nn.ModuleList([
            ConvBlock(1, 32),
            ConvBlock(32, 32),
            ConvBlock(32, 32),
            ConvBlock(32, 64),
            ConvBlock(64, 64),
            ConvBlock(64, 64),
            ConvBlock(64, 128),
            ConvBlock(128, 128),
            ConvBlock(128, 128),
            ConvBlock(128, 256),
            ConvBlock(256, 256),
            ConvBlock(256, 256),
            ConvBlock(256, 512),
        ])
        
        # 解码器块 - 匹配预训练权重的结构
        self.face_decoder_blocks = nn.ModuleList([
            nn.Sequential(
                ConvBlock(512, 512),
                ConvBlock(512, 512),
                ConvBlock(512, 512),
            ),
            nn.Sequential(
                ConvBlock(512, 256),
                ConvBlock(256, 256),
                ConvBlock(256, 256),
            ),
            nn.Sequential(
                ConvBlock(256, 128),
                ConvBlock(128, 128),
                ConvBlock(128, 128),
            ),
        ])
        
        # 输出块
        self.output_block = nn.Sequential(
            ConvBlock(128, 32),
            nn.Conv2d(32, 3, kernel_size=1, stride=1, padding=0),
            nn.Sigmoid()
        )

    def forward(self, mel, face):
        # 确保输入维度正确
        if face.size(1) == 3:
            face = torch.cat([face, face], dim=1)  # 复制通道以得到6通道输入
            
        # 面部特征提取
        x = face
        face_features = []
        for block in self.face_encoder_blocks:
            x = block(x)
            face_features.append(x)
            
        # 音频特征提取
        a = mel.unsqueeze(1)  # 添加通道维度
        for layer in self.audio_encoder:
            a = layer(a)
            
        # 特征融合
        x = torch.cat([face_features[-1], a], dim=1)
        
        # 解码生成
        for block in self.face_decoder_blocks:
            x = block(x)
            
        # 生成最终输出
        x = self.output_block(x)
        return x

# 创建单例实例
face_model = FaceAnimationModel() 