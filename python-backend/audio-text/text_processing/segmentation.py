"""
文本分段处理模块
"""
import re
import os
import json
import jieba
import jieba.analyse

class TextSegmenter:
    """文本分段处理类"""
    
    def __init__(self, min_segment_length=50, max_segment_length=500):
        """
        初始化文本分段器
        
        Args:
            min_segment_length: 最小分段长度
            max_segment_length: 最大分段长度
        """
        self.min_segment_length = min_segment_length
        self.max_segment_length = max_segment_length
        
        # 加载结巴分词词典
        jieba.initialize()
    
    def segment_by_meaning(self, text):
        """
        按照语义进行文本分段
        
        Args:
            text: 待分段文本
            
        Returns:
            分段后的文本列表
        """
        # 首先按句子分割
        sentences = self._split_into_sentences(text)
        
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            # 如果当前分段加上新句子超过最大长度，则保存当前分段
            if len(current_segment) + len(sentence) > self.max_segment_length and len(current_segment) >= self.min_segment_length:
                segments.append(current_segment.strip())
                current_segment = ""
            
            current_segment += sentence
            
            # 检查是否是段落结束（如果句子以句号、问号、感叹号结束，且当前分段长度已达到最小长度）
            if (sentence.strip().endswith(("。", "！", "？", ".", "!", "?")) and 
                len(current_segment) >= self.min_segment_length):
                segments.append(current_segment.strip())
                current_segment = ""
        
        # 添加最后一个分段（如果有）
        if current_segment.strip():
            segments.append(current_segment.strip())
        
        return segments
    
    def _split_into_sentences(self, text):
        """
        将文本分割为句子
        
        Args:
            text: 待分割文本
            
        Returns:
            句子列表
        """
        # 使用正则表达式分割句子
        pattern = r'([。！？\.!?])'
        sentences = []
        
        # 分割文本
        parts = re.split(pattern, text)
        
        # 重新组合句子（保留标点符号）
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                sentences.append(parts[i] + parts[i+1])
            else:
                sentences.append(parts[i])
        
        return sentences
    
    def add_tags(self, segments):
        """
        为分段文本添加标签
        
        Args:
            segments: 分段文本列表
            
        Returns:
            带标签的分段文本列表，格式为[{text: "...", tags: ["tag1", "tag2", ...]}]
        """
        tagged_segments = []
        
        for segment in segments:
            # 使用结巴分词提取关键词作为标签
            tags = jieba.analyse.extract_tags(segment, topK=5)
            
            tagged_segments.append({
                "text": segment,
                "tags": tags
            })
        
        return tagged_segments
    
    def process_text(self, text, output_file=None):
        """
        处理文本：分段并添加标签
        
        Args:
            text: 待处理文本
            output_file: 输出文件路径，None表示自动生成
            
        Returns:
            (处理后的分段文本, 输出文件路径)
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
                
            output_file = os.path.join(output_dir, f"segments_{int(os.path.getmtime(output_dir))}.json")
        
        # 保存处理结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tagged_segments, f, ensure_ascii=False, indent=2)
        
        print(f"分段结果已保存到: {output_file}")
        return tagged_segments, output_file
