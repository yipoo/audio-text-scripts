import numpy as np
from typing import List, Dict, Tuple
import torch
import pypinyin
from pypinyin import lazy_pinyin, Style

class ChineseVisemeMapper:
    """中文音素到 Viseme 的映射器"""
    
    # 定义中文拼音到音素的映射
    PINYIN_TO_PHONEME = {
        # 声母
        'b': ['b'], 'p': ['p'], 'm': ['m'], 'f': ['f'],
        'd': ['d'], 't': ['t'], 'n': ['n'], 'l': ['l'],
        'g': ['g'], 'k': ['k'], 'h': ['h'],
        'j': ['j'], 'q': ['q'], 'x': ['x'],
        'zh': ['zh'], 'ch': ['ch'], 'sh': ['sh'], 'r': ['r'],
        'z': ['z'], 'c': ['c'], 's': ['s'],
        # 韵母
        'a': ['a'], 'o': ['o'], 'e': ['e'], 'i': ['i'],
        'u': ['u'], 'v': ['v'], 'ai': ['a', 'i'],
        'ei': ['e', 'i'], 'ao': ['a', 'o'], 'ou': ['o', 'u'],
        'an': ['a', 'n'], 'en': ['e', 'n'], 'ang': ['a', 'ng'],
        'eng': ['e', 'ng'], 'er': ['e', 'r'],
        'yi': ['i'], 'wu': ['u'], 'yu': ['v'],
        'yin': ['i', 'n'], 'yun': ['v', 'n'],
        'ying': ['i', 'ng'], 'wang': ['u', 'a', 'ng'],
        
        # 完整拼音
        'mei': ['m', 'ei'], 'bu': ['b', 'u'], 'guo': ['g', 'uo'], 
        'xuan': ['x', 'uan'], 'cui': ['c', 'ui'], 'hui': ['h', 'ui'],
        'hu': ['h', 'u'], 'sai': ['s', 'ai'], 'wu': ['w', 'u'],
        'zhuang': ['zh', 'uang'], 'zong': ['z', 'ong'],
        'cheng': ['ch', 'eng'], 'gong': ['g', 'ong'],
        'da': ['d', 'a'], 'ji': ['j', 'i'], 'qi': ['q', 'i'],
        'guan': ['g', 'uan'], 'jian': ['j', 'ian'], 'ling': ['l', 'ing'],
        'dao': ['d', 'ao'], 'ceng': ['c', 'eng'], 'bao': ['b', 'ao'],
        'kuo': ['k', 'uo'], 'dan': ['d', 'an'], 'zhuan': ['zh', 'uan'],
        'jia': ['j', 'ia'], 'jun': ['j', 'un'], 'sheng': ['sh', 'eng'],
        'dui': ['d', 'ui'], 'shi': ['sh', 'i'], 'xing': ['x', 'ing'],
        'dong': ['d', 'ong'], 'zeng': ['z', 'eng'], 'pai': ['p', 'ai'],
        'hang': ['h', 'ang'], 'mu': ['m', 'u'], 'shuang': ['sh', 'uang'],
        'zuo': ['z', 'uo'], 'zhan': ['zh', 'an'], 'shu': ['sh', 'u'],
        
        # 单韵母拼音
        'uo': ['u', 'o'], 'ia': ['i', 'a'], 'ui': ['u', 'i'],
        'uan': ['u', 'an'], 'uang': ['u', 'ang'], 'ong': ['o', 'ng'],
        'ian': ['i', 'an'], 'ing': ['i', 'ng'], 'un': ['u', 'n'],
        
        # 标点符号
        '，': [], '。': [], '！': [], '？': [], '：': [], '；': [],
        '、': [], '"': [], '"': [], ''': [], ''': [], '（': [], '）': [],
        '-': [], '_': [], '=': [], '+': [], '*': [], '&': [], '^': [],
        '%': [], '$': [], '#': [], '@': [], '!': [], ' ': [], '\n': [],
        '.': [], ',': [], ':': [], ';': [], '?': [], '<': [], '>': [],
        '~': [], '`': [], '\t': [], '|': [], '\\': [], '/': [],
        '[': [], ']': [], '{': [], '}': []
    }
    
    # 定义音素到 Viseme 的映射（基于 Preston Blair 的 12个基本口型）
    PHONEME_TO_VISEME = {
        # 闭合音素
        'b': 0, 'p': 0, 'm': 0,
        # 唇齿音素
        'f': 1, 'v': 1,
        # 齿音
        'd': 2, 't': 2, 'n': 2, 'l': 2,
        # 齿龈音
        's': 3, 'z': 3,
        # 舌面音
        'sh': 4, 'zh': 4, 'ch': 4,
        # 舌根音
        'g': 5, 'k': 5, 'ng': 5,
        # 元音
        'a': 6, 'ai': 6, 'ao': 6,
        'e': 7, 'ei': 7,
        'i': 8, 'yi': 8,
        'o': 9, 'ou': 9,
        'u': 10, 'wu': 10,
        'v': 11, 'yu': 11
    }
    
    # 定义 Viseme 到嘴型关键点的映射
    VISEME_TO_LANDMARKS = {
        0: np.array([  # 闭合
            [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0],
            [0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]
        ], dtype=np.float64),
        1: np.array([  # 唇齿 (f, v) - 上唇贴下齿
            [0.0, 0.0], [0.1, 0.0], [0.0, 0.1], [-0.1, 0.0],
            [0.0, -0.1], [0.05, 0.1], [0.0, 0.15], [-0.05, 0.1]
        ], dtype=np.float64),
        2: np.array([  # 齿音 (d, t, n, l) - 舌尖抵上齿
            [0.0, -0.05], [0.15, 0.0], [0.0, 0.1], [-0.15, 0.0],
            [0.0, -0.1], [0.1, 0.05], [0.0, 0.2], [-0.1, 0.05]
        ], dtype=np.float64),
        3: np.array([  # 齿龈音 (s, z) - 唇稍微开启，齿接近
            [0.0, -0.05], [0.2, -0.05], [0.0, 0.05], [-0.2, -0.05],
            [0.0, -0.05], [0.15, 0.0], [0.0, 0.1], [-0.15, 0.0]
        ], dtype=np.float64),
        4: np.array([  # 舌面音 (sh, zh, ch) - 唇稍微突出
            [0.0, -0.1], [0.15, -0.05], [0.0, 0.05], [-0.15, -0.05],
            [0.0, -0.15], [0.1, 0.0], [0.0, 0.2], [-0.1, 0.0]
        ], dtype=np.float64),
        5: np.array([  # 舌根音 (g, k, ng) - 后部口腔收缩
            [0.0, -0.1], [0.2, 0.0], [0.0, 0.1], [-0.2, 0.0],
            [0.0, -0.1], [0.15, 0.05], [0.0, 0.2], [-0.15, 0.05]
        ], dtype=np.float64),
        6: np.array([  # 元音 (a, ai, ao) - 大开口
            [0.0, -0.15], [0.25, -0.1], [0.0, 0.2], [-0.25, -0.1],
            [0.0, -0.2], [0.2, 0.0], [0.0, 0.3], [-0.2, 0.0]
        ], dtype=np.float64),
        7: np.array([  # 元音 (e, ei) - 中等开口
            [0.0, -0.1], [0.2, -0.05], [0.0, 0.15], [-0.2, -0.05],
            [0.0, -0.15], [0.15, 0.05], [0.0, 0.25], [-0.15, 0.05]
        ], dtype=np.float64),
        8: np.array([  # 元音 (i, yi) - 扁平开口，嘴角微扯
            [0.0, -0.05], [0.3, -0.05], [0.0, 0.05], [-0.3, -0.05],
            [0.0, -0.05], [0.25, 0.0], [0.0, 0.1], [-0.25, 0.0]
        ], dtype=np.float64),
        9: np.array([  # 元音 (o, ou) - 圆唇中等开口
            [0.0, -0.15], [0.15, -0.15], [0.0, 0.15], [-0.15, -0.15],
            [0.0, -0.2], [0.1, -0.1], [0.0, 0.25], [-0.1, -0.1]
        ], dtype=np.float64),
        10: np.array([  # 元音 (u, wu) - 突出圆唇
            [0.0, -0.2], [0.1, -0.2], [0.0, 0.1], [-0.1, -0.2],
            [0.0, -0.25], [0.05, -0.2], [0.0, 0.15], [-0.05, -0.2]
        ], dtype=np.float64),
        11: np.array([  # 元音 (v, yu) - 扁平突出圆唇
            [0.0, -0.2], [0.1, -0.15], [0.0, 0.1], [-0.1, -0.15],
            [0.0, -0.25], [0.05, -0.1], [0.0, 0.15], [-0.05, -0.1]
        ], dtype=np.float64)
    }
    
    def __init__(self):
        """初始化映射器"""
        self.cached_visemes = {}
    
    def text_to_pinyin(self, text: str) -> List[str]:
        """将中文文本转换为拼音序列"""
        return lazy_pinyin(text, style=Style.NORMAL)
    
    def pinyin_to_phonemes(self, pinyin: str) -> List[str]:
        """将拼音转换为音素序列"""
        if pinyin in self.PINYIN_TO_PHONEME:
            return self.PINYIN_TO_PHONEME[pinyin]
        return []
    
    def phoneme_to_viseme(self, phoneme: str) -> int:
        """将音素转换为 Viseme ID"""
        return self.PHONEME_TO_VISEME.get(phoneme, 0)  # 默认返回闭合嘴型
    
    def get_viseme_landmarks(self, viseme_id: int) -> np.ndarray:
        """获取指定 Viseme 的嘴型关键点"""
        return self.VISEME_TO_LANDMARKS.get(viseme_id, self.VISEME_TO_LANDMARKS[0])
    
    def get_transition_landmarks(self, start_viseme: int, end_viseme: int, 
                               progress: float) -> np.ndarray:
        """计算两个 Viseme 之间的过渡关键点"""
        # 获取起始和结束的嘴型关键点，确保是浮点数类型
        start_landmarks = self.get_viseme_landmarks(start_viseme).astype(np.float64)
        end_landmarks = self.get_viseme_landmarks(end_viseme).astype(np.float64)
        
        # 确保 progress 是浮点数，并在 0-1 范围内
        progress = float(max(0.0, min(1.0, progress)))
        
        # 使用线性插值计算过渡关键点
        transition = start_landmarks + (end_landmarks - start_landmarks) * progress
        
        return transition.astype(np.float64)  # 确保返回浮点数类型
    
    def text_to_visemes(self, text: str) -> List[int]:
        """将文本转换为 Viseme 序列"""
        if not text or len(text.strip()) == 0:
            print("警告: 输入文本为空")
            return [0]  # 返回闭合嘴型
        
        if text in self.cached_visemes:
            return self.cached_visemes[text]
        
        visemes = []
        
        try:
            # 将文本转换为拼音
            print(f"处理文本: {text}")
            pinyin_seq = self.text_to_pinyin(text)
            print(f"拼音序列: {pinyin_seq}")
            
            for pinyin in pinyin_seq:
                phonemes = self.pinyin_to_phonemes(pinyin)
                if not phonemes:
                    # 如果找不到拼音映射，则使用默认元音
                    print(f"未找到拼音映射: {pinyin}，使用默认元音")
                    phonemes = ['a']
                    
                for phoneme in phonemes:
                    viseme = self.phoneme_to_viseme(phoneme)
                    visemes.append(viseme)
                    
            # 确保至少有一个 viseme
            if not visemes:
                print("警告: 未生成任何 viseme，使用默认嘴型")
                visemes = [6]  # 使用大开口元音作为默认
                
            # 添加开始和结束的闭合嘴型
            visemes = [0] + visemes + [0]
            
            print(f"生成的 viseme 序列: {visemes}")
            self.cached_visemes[text] = visemes
            return visemes
            
        except Exception as e:
            print(f"文本转换为 viseme 序列失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return [0, 6, 0]  # 返回一个基本序列：闭合-开口-闭合
    
    def generate_landmarks_sequence(self, text: str, duration: float, 
                                  fps: int = 30) -> List[np.ndarray]:
        """生成给定文本的嘴型关键点序列"""
        visemes = self.text_to_visemes(text)
        total_frames = int(duration * fps)
        
        if not visemes:
            # 返回闭合嘴型的序列，确保是浮点数类型
            return [self.get_viseme_landmarks(0).astype(np.float64)] * total_frames
        
        # 计算每个 Viseme 的持续时间
        viseme_duration = duration / len(visemes)
        frames_per_viseme = total_frames / len(visemes)
        
        landmarks_sequence = []
        for frame_idx in range(total_frames):
            # 计算当前帧所在的 Viseme 位置
            viseme_idx = min(int(frame_idx / frames_per_viseme), len(visemes) - 1)
            next_viseme_idx = min(viseme_idx + 1, len(visemes) - 1)
            
            # 计算过渡进度
            if frames_per_viseme > 0:
                progress = (frame_idx % frames_per_viseme) / frames_per_viseme
            else:
                progress = 0.0
            
            # 生成当前帧的关键点
            landmarks = self.get_transition_landmarks(
                visemes[viseme_idx],
                visemes[next_viseme_idx],
                progress
            ).astype(np.float64)  # 确保是浮点数类型
            
            landmarks_sequence.append(landmarks)
        
        return landmarks_sequence

# 创建单例实例
viseme_mapper = ChineseVisemeMapper() 