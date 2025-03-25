import torch
import torch.nn as nn
import torch.nn.functional as F

class Conv2d(nn.Module):
    def __init__(self, cin, cout, kernel_size, stride, padding, residual=False):
        super().__init__()
        self.conv_block = nn.Sequential(
            nn.Conv2d(cin, cout, kernel_size, stride, padding),
            nn.BatchNorm2d(cout),
            nn.ReLU(inplace=True)
        )
        self.residual = residual

    def forward(self, x):
        out = self.conv_block(x)
        if self.residual:
            out += x
        return out

class Wav2Lip(nn.Module):
    def __init__(self):
        super(Wav2Lip, self).__init__()

        # 面部编码器块 - 完全匹配预训练权重结构
        self.face_encoder_blocks = nn.ModuleList([
            nn.ModuleList([
                Conv2d(6, 16, kernel_size=7, stride=1, padding=3),
            ]),
            nn.ModuleList([
                Conv2d(16, 32, kernel_size=3, stride=2, padding=1),
                Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
            nn.ModuleList([
                Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
                Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
            nn.ModuleList([
                Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
                Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
            nn.ModuleList([
                Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
                Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
        ])

        # 音频编码器 - 匹配预训练权重结构
        self.audio_encoder = nn.ModuleList([
            Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(32, 64, kernel_size=3, stride=(3, 1), padding=1),
            Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(64, 128, kernel_size=3, stride=3, padding=1),
            Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(128, 256, kernel_size=3, stride=(3, 2), padding=1),
            Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            Conv2d(512, 512, kernel_size=1, stride=1, padding=0),
        ])

        # 解码器块 - 完全匹配预训练权重结构
        self.face_decoder_blocks = nn.ModuleList([
            nn.ModuleList([
                Conv2d(512, 512, kernel_size=1, stride=1, padding=0),
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
            nn.ModuleList([
                Conv2d(768, 512, kernel_size=3, stride=1, padding=1),  # 修正输入通道
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
            nn.ModuleList([
                Conv2d(768, 512, kernel_size=3, stride=1, padding=1),  # 修正输入通道
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
            nn.ModuleList([
                Conv2d(512, 384, kernel_size=3, stride=1, padding=1),  # 修正通道数
                Conv2d(384, 384, kernel_size=3, stride=1, padding=1),
                Conv2d(384, 384, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
            nn.ModuleList([
                Conv2d(384, 256, kernel_size=3, stride=1, padding=1),  # 修正通道数
                Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
                Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
            nn.ModuleList([
                Conv2d(256, 128, kernel_size=3, stride=1, padding=1),  # 修正通道数
                Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
                Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
            nn.ModuleList([
                Conv2d(128, 64, kernel_size=3, stride=1, padding=1),  # 修正通道数
                Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
                Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
            ]),
        ])

        # 输出块
        self.output_block = nn.Sequential(
            Conv2d(64, 32, kernel_size=3, stride=1, padding=1),  # 修正输入通道
            nn.Conv2d(32, 3, kernel_size=1, stride=1, padding=0),
            nn.Sigmoid()
        )

    def forward(self, audio_sequences, face_sequences):
        # 面部特征提取
        face_embedding = face_sequences
        face_feature_maps = []
        for f in self.face_encoder_blocks:
            for block in f:
                face_embedding = block(face_embedding)
            face_feature_maps.append(face_embedding)

        # 音频特征提取
        audio_embedding = audio_sequences.unsqueeze(1)
        for block in self.audio_encoder:
            audio_embedding = block(audio_embedding)

        # 特征融合
        audio_embedding = F.interpolate(audio_embedding, size=face_embedding.shape[2:])
        embedding = torch.cat([audio_embedding, face_embedding], dim=1)

        # 解码生成
        for i, f in enumerate(self.face_decoder_blocks):
            for j, block in enumerate(f):
                if j == 0 and i > 0:  # 第一个块之后的所有块
                    embedding = torch.cat([embedding, face_feature_maps[-1-i]], dim=1)
                embedding = block(embedding)
            if i < len(self.face_decoder_blocks) - 1:  # 除了最后一个块
                embedding = F.interpolate(embedding, scale_factor=2)

        # 生成最终输出
        output = self.output_block(embedding)
        return output

def load_wav2lip_model(checkpoint_path, device='cpu'):
    model = Wav2Lip()
    checkpoint = torch.load(checkpoint_path, map_location=device)
    s = checkpoint["state_dict"]
    new_s = {}
    for k, v in s.items():
        new_s[k.replace('.net', '')] = v
    model.load_state_dict(new_s, strict=True)
    model.eval()
    return model 