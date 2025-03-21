"""
文本分段处理模块
"""
import os
import json
import jieba
from datetime import datetime

class TextSegmenter:
    """文本分段处理类"""
    
    def __init__(self, min_segment_length=50, max_segment_length=500):
        """
        初始化分段处理器
        
        Args:
            min_segment_length: 最小分段长度（字符数）
            max_segment_length: 最大分段长度（字符数）
        """
        self.min_segment_length = min_segment_length
        self.max_segment_length = max_segment_length
        
    def segment_by_meaning(self, text):
        """
        按意思分段文本
        
        Args:
            text: 要分段的文本
            
        Returns:
            分段后的文本列表
        """
        # 使用标点符号和句子长度进行分段
        segments = []
        current_segment = ""
        
        # 按句号、问号、感叹号等分割
        sentences = []
        temp = ""
        for char in text:
            temp += char
            if char in ['。', '！', '？', '…', '.', '!', '?']:
                sentences.append(temp)
                temp = ""
        
        if temp:  # 添加最后一个句子（如果没有标点符号结尾）
            sentences.append(temp)
        
        # 合并短句，分割长句
        for sentence in sentences:
            if len(current_segment) + len(sentence) <= self.max_segment_length:
                current_segment += sentence
            else:
                if current_segment and len(current_segment) >= self.min_segment_length:
                    segments.append(current_segment)
                
                # 如果单个句子超过最大长度，需要进一步分割
                if len(sentence) > self.max_segment_length:
                    # 简单地按字符数分割
                    for i in range(0, len(sentence), self.max_segment_length):
                        segment = sentence[i:i+self.max_segment_length]
                        if len(segment) >= self.min_segment_length:
                            segments.append(segment)
                else:
                    current_segment = sentence
        
        # 添加最后一个分段
        if current_segment and len(current_segment) >= self.min_segment_length:
            segments.append(current_segment)
            
        return segments
    
    def add_tags(self, segments):
        """
        为分段添加标签
        
        Args:
            segments: 分段文本列表
            
        Returns:
            带标签的分段列表，格式为[{text: "...", tags: ["tag1", "tag2", ...]}]
        """
        tagged_segments = []
        
        for segment in segments:
            # 使用jieba提取关键词作为标签
            tags = jieba.analyse.extract_tags(segment, topK=5)
            
            # 如果提取不到关键词，使用分词结果中的名词、动词等
            if not tags:
                words = jieba.posseg.cut(segment)
                tags = [word for word, flag in words if flag.startswith('n') or flag.startswith('v')][:5]
            
            # 添加到结果列表
            tagged_segments.append({
                "text": segment,
                "tags": tags
            })
        
        return tagged_segments
    
    def process_text(self, text, output_file=None):
        """
        处理文本：分段并添加标签
        
        Args:
            text: 要处理的文本
            output_file: 输出文件路径，None表示自动生成
            
        Returns:
            (处理结果, 输出文件路径)
        """
        # 分段
        segments = self.segment_by_meaning(text)
        
        # 添加标签
        tagged_segments = self.add_tags(segments)
        
        # 如果未指定输出文件，则自动生成
        if output_file is None:
            output_dir = "segments"
            
            # 确保输出目录存在
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"segments_{timestamp}.json")
        
        # 保存处理结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tagged_segments, f, ensure_ascii=False, indent=2)
        
        print(f"分段结果已保存到: {output_file}")
        return tagged_segments, output_file
