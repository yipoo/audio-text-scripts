"""
文本标签生成模块
"""
import jieba.analyse

class TextTagger:
    """文本标签生成类"""
    
    def __init__(self, topK=5):
        """
        初始化标签生成器
        
        Args:
            topK: 提取的关键词数量
        """
        self.topK = topK
    
    def extract_tags(self, text):
        """
        提取文本中的关键词作为标签
        
        Args:
            text: 文本内容
            
        Returns:
            标签列表
        """
        # 使用TF-IDF算法提取关键词
        tags = jieba.analyse.extract_tags(text, topK=self.topK)
        
        # 如果提取不到关键词，使用TextRank算法
        if not tags:
            tags = jieba.analyse.textrank(text, topK=self.topK)
        
        # 如果仍然提取不到，使用分词结果中的名词、动词等
        if not tags:
            words = jieba.posseg.cut(text)
            tags = [word for word, flag in words if flag.startswith('n') or flag.startswith('v')][:self.topK]
        
        return tags
    
    def tag_segments(self, segments):
        """
        为多个文本分段添加标签
        
        Args:
            segments: 文本分段列表
            
        Returns:
            带标签的分段列表，格式为[{text: "...", tags: ["tag1", "tag2", ...]}]
        """
        tagged_segments = []
        
        for segment in segments:
            tags = self.extract_tags(segment)
            tagged_segments.append({
                "text": segment,
                "tags": tags
            })
        
        return tagged_segments
