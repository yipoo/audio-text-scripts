"""
AI内容创作模块 - 使用阿里云DeepSeek模型
"""
import os
import json
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('content_creator')

# 尝试导入dashscope
try:
    import dashscope
    from dashscope import Generation
    USE_DASHSCOPE = True
    logger.info("成功导入阿里云DashScope SDK")
except ImportError as e:
    USE_DASHSCOPE = False
    logger.error(f"阿里云DashScope SDK导入失败: {str(e)}")
    logger.error("请确保已安装阿里云DashScope SDK: pip install dashscope")

from utils.config import ALIYUN_DASHSCOPE_API_KEY

class ContentCreator:
    """AI内容创作类，使用阿里云DeepSeek模型"""
    
    def __init__(self, model="qwen-max"):
        """
        初始化内容创作器
        
        Args:
            model: 使用的模型名称，默认为qwen-max
        """
        self.model = model
        logger.info(f"初始化内容创作器，使用模型: {model}")
        logger.info(f"ALIYUN_DASHSCOPE_API_KEY: {ALIYUN_DASHSCOPE_API_KEY[:3]}...{ALIYUN_DASHSCOPE_API_KEY[-3:] if ALIYUN_DASHSCOPE_API_KEY else 'None'}")
        
        if not ALIYUN_DASHSCOPE_API_KEY:
            logger.error("API密钥未正确配置，请检查.env文件")
            raise ValueError("API密钥未正确配置，请检查.env文件")
            
        if USE_DASHSCOPE:
            logger.info("使用阿里云DashScope SDK进行内容创作")
            dashscope.api_key = ALIYUN_DASHSCOPE_API_KEY
        else:
            logger.error("阿里云DashScope SDK不可用，请安装SDK")
            raise ImportError("阿里云DashScope SDK不可用，请安装SDK")
    
    def generate_content(self, prompt, max_tokens=1000, temperature=0.7, top_p=0.8):
        """
        生成内容
        
        Args:
            prompt: 提示词
            max_tokens: 最大生成token数
            temperature: 温度参数
            top_p: top-p参数
            
        Returns:
            生成的内容
        """
        logger.info(f"生成内容，提示词: {prompt[:50]}...")
        
        try:
            # 使用DashScope SDK生成内容
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            
            # 检查响应
            if response.status_code == 200:
                result = response.output.text
                logger.info(f"生成成功，结果: {result[:50]}...")
                return result
            else:
                logger.error(f"生成失败: {response.code}, {response.message}")
                raise Exception(f"生成失败: {response.message}")
                
        except Exception as e:
            logger.error(f"生成内容出错: {str(e)}")
            raise
    
    def process_segment(self, segment, output_format="markdown"):
        """
        处理单个文本段落
        
        Args:
            segment: 文本段落
            output_format: 输出格式，默认为markdown
            
        Returns:
            处理结果
        """
        logger.info(f"处理文本段落: {segment['text'][:50]}...")
        
        # 构建提示词
        prompt = self._build_prompt(segment, output_format)
        
        # 生成内容
        result = self.generate_content(prompt)
        
        return {
            "segment": segment,
            "prompt": prompt,
            "result": result
        }
    
    def _build_prompt(self, segment, output_format):
        """构建提示词"""
        text = segment.get("text", "")
        tags = segment.get("tags", [])
        
        # 构建提示词
        prompt = f"""
你是一位专业的直播内容创作者，请根据以下文本内容进行创意加工，生成适合直播平台的内容。

原始文本：
{text}

标签：{', '.join(tags) if tags else '无'}

要求：
1. 保持原始文本的核心信息和观点
2. 使用更加生动、吸引人的表达方式
3. 增加一些互动元素或号召性用语
4. 使用口语化的语言，增加亲和力
5. 输出格式为{output_format}

请直接输出创作后的内容，不要包含解释：
"""
        
        return prompt
    
    def process_segments(self, segments, output_file=None):
        """
        处理多个文本段落
        
        Args:
            segments: 文本段落列表
            output_file: 输出文件路径，None表示不保存
            
        Returns:
            (处理结果, 输出文件路径)
        """
        logger.info(f"处理{len(segments)}个文本段落")
        
        results = []
        for i, segment in enumerate(segments):
            logger.info(f"处理段落[{i+1}/{len(segments)}]")
            result = self.process_segment(segment)
            results.append(result)
        
        # 如果指定了输出文件，保存结果
        if output_file:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # 保存结果
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"处理结果已保存到: {output_file}")
        
        return results, output_file
    
    def process_file(self, input_file, output_file=None):
        """
        处理文本文件
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径，None表示自动生成
            
        Returns:
            (处理结果, 输出文件路径)
        """
        # 确保输入文件存在
        if not os.path.exists(input_file):
            logger.error(f"输入文件不存在: {input_file}")
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        
        # 如果没有指定输出文件，自动生成
        if output_file is None:
            base_name = os.path.basename(input_file)
            name_without_ext = os.path.splitext(base_name)[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{name_without_ext}_generated_{timestamp}.json"
        
        logger.info(f"处理文件: {input_file}")
        logger.info(f"输出文件: {output_file}")
        
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            if input_file.endswith('.json'):
                # JSON文件，读取为段落列表
                segments = json.load(f)
            else:
                # 文本文件，作为单个段落处理
                text = f.read()
                segments = [{"text": text, "tags": []}]
        
        # 处理段落
        return self.process_segments(segments, output_file)
    
    def generate_multiple_scripts(self, text, tags=None, num_scripts=5, custom_prompt=None):
        """
        生成多个脚本
        
        Args:
            text: 原始文本
            tags: 标签列表，默认为None
            num_scripts: 要生成的脚本数量，默认为5
            custom_prompt: 自定义提示词，默认为None
            
        Returns:
            生成的脚本列表
        """
        logger.info(f"生成{num_scripts}个脚本，基于文本: {text[:50]}...")
        
        scripts = []
        
        # 处理标签
        if tags is None:
            tags = []
        
        # 使用自定义提示词或默认提示词
        if custom_prompt:
            # 直接使用自定义提示词
            prompt = custom_prompt
        else:
            # 使用默认提示词
            prompt = f"""
你是一位专业的直播内容创作者，请根据以下文本内容和标签，生成{num_scripts}个不同风格的直播脚本。

原始文本：
{text}

标签：{', '.join(tags) if tags else '无'}

要求：
1. 生成{num_scripts}个不同的脚本，每个脚本风格各异
2. 保持原始文本的核心信息和主要观点
3. 使用更加生动、吸引人的表达方式
4. 增加一些互动元素或号召性用语
5. 使用口语化的语言，增加亲和力
6. 每个脚本用"---"分隔

请直接输出创作后的内容，不要包含解释：
"""
        
        try:
            # 生成内容
            result = self.generate_content(prompt, max_tokens=3000, temperature=0.8)
            
            # 解析结果
            if result:
                # 按分隔符分割脚本
                script_list = result.split("---")
                
                # 清理每个脚本
                for script in script_list:
                    script = script.strip()
                    if script:
                        scripts.append(script)
                
                # 限制数量
                scripts = scripts[:num_scripts]
                
                logger.info(f"成功生成 {len(scripts)} 个脚本")
            else:
                logger.warning("生成结果为空")
                
        except Exception as e:
            logger.error(f"生成多个脚本出错: {str(e)}")
            
        return scripts
    
    def process_multiple_scripts(self, input_text, num_scripts=5, output_file=None):
        """
        处理文本并生成多个脚本
        
        Args:
            input_text: 输入文本
            num_scripts: 要生成的脚本数量，默认为5
            output_file: 输出文件路径，None表示自动生成
            
        Returns:
            (生成的脚本列表, 输出文件路径)
        """
        # 如果没有指定输出文件，自动生成
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/multiple_scripts_{timestamp}.json"
        
        logger.info(f"处理文本并生成{num_scripts}个脚本")
        logger.info(f"输出文件: {output_file}")
        
        # 生成脚本
        scripts = self.generate_multiple_scripts(input_text, num_scripts=num_scripts)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 保存结果
        result = {
            "original_text": input_text,
            "scripts": scripts
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"生成的{len(scripts)}个脚本已保存到: {output_file}")
        
        return scripts, output_file
    
    def generate_script(self, text, output_format="markdown"):
        """
        生成单份话术
        
        Args:
            text: 原始文本
            output_format: 输出格式，默认为markdown
            
        Returns:
            生成的话术
        """
        logger.info(f"生成话术，基于文本: {text[:50]}...")
        
        # 构建提示词
        prompt = f"""
请基于以下内容，生成一份优化的话术。保持原始内容的核心信息，但使用更生动、吸引人的表达方式。

原始内容：
{text}

要求：
1. 保持原始内容的核心信息和主要观点
2. 使用更加生动、吸引人的表达方式
3. 增加一些互动元素或号召性用语
4. 适当添加一些表情符号增加亲和力
5. 输出格式为{output_format}

请直接输出创作后的内容，不要包含解释:
"""
        
        # 生成内容
        result = self.generate_content(prompt)
        
        return result
