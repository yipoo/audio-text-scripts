#!/usr/bin/env python3
"""
测试阿里云API连接
"""
import os
import logging
import json
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_api')

# 加载环境变量
load_dotenv()

def test_nls_api():
    """测试阿里云语音识别API连接"""
    logger.info("测试阿里云语音识别API连接...")
    
    # 检查环境变量
    access_key_id = os.getenv('ALIYUN_ACCESS_KEY_ID')
    access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
    app_key = os.getenv('ALIYUN_APPKEY')
    region = os.getenv('ALIYUN_REGION', 'cn-shanghai')
    
    # 检查环境变量是否设置
    if not access_key_id or not access_key_secret or not app_key:
        logger.error("阿里云语音识别API环境变量未设置")
        logger.error("请确保以下环境变量已设置:")
        logger.error("ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_APPKEY")
        return False
    
    logger.info(f"ALIYUN_ACCESS_KEY_ID: {access_key_id[:3]}...{access_key_id[-3:]}")
    logger.info(f"ALIYUN_ACCESS_KEY_SECRET: {access_key_secret[:3]}...{access_key_secret[-3:]}")
    logger.info(f"ALIYUN_APPKEY: {app_key}")
    logger.info(f"ALIYUN_REGION: {region}")
    
    try:
        # 尝试导入阿里云NLS SDK
        import nls
        from nls.token import getToken
        
        logger.info("成功导入阿里云NLS SDK")
        
        # 获取Token
        token = getToken(access_key_id, access_key_secret)
        if not token:
            logger.error("获取Token失败")
            return False
        
        logger.info(f"成功获取Token: {token[:10]}...")
        
        # 定义回调函数
        def on_start(message, *args):
            logger.info(f"识别开始: {message}")
            
        def on_error(message, *args):
            logger.error(f"识别错误: {message}")
            
        def on_close(*args):
            logger.info("连接关闭")
            
        def on_result_changed(message, *args):
            logger.info(f"识别结果变化: {message}")
            
        def on_completed(message, *args):
            logger.info(f"识别完成: {message}")
        
        # 创建识别对象
        sr = nls.NlsSpeechRecognizer(
            token=token,
            appkey=app_key,
            on_start=on_start,
            on_result_changed=on_result_changed,
            on_completed=on_completed,
            on_error=on_error,
            on_close=on_close
        )
        
        logger.info("NLS连接测试成功")
        return True
            
    except Exception as e:
        logger.error(f"阿里云语音识别API测试出错: {str(e)}")
        return False

def test_dashscope_api():
    """测试阿里云DashScope API连接"""
    logger.info("测试阿里云DashScope API连接...")
    
    # 检查环境变量
    api_key = os.getenv('ALIYUN_DASHSCOPE_API_KEY')
    
    # 检查环境变量是否设置
    if not api_key:
        logger.error("阿里云DashScope API密钥未设置")
        logger.error("请确保以下环境变量已设置:")
        logger.error("ALIYUN_DASHSCOPE_API_KEY")
        return False
    
    logger.info(f"ALIYUN_DASHSCOPE_API_KEY: {api_key[:3]}...{api_key[-3:]}")
    
    try:
        # 尝试导入DashScope SDK
        import dashscope
        
        logger.info("成功导入阿里云DashScope SDK")
        
        # 设置API密钥
        dashscope.api_key = api_key
        
        # 创建简单的测试提示词
        prompt = "你好，请用一句话介绍一下你自己。"
        
        # 发送请求
        logger.info("发送测试请求...")
        from dashscope import Generation
        
        response = Generation.call(
            model="qwen-max",
            prompt=prompt
        )
        
        # 检查响应
        if response.status_code == 200:
            logger.info(f"阿里云DashScope API连接成功，返回结果: {response.output.text[:50]}...")
            return True
        else:
            logger.error(f"阿里云DashScope API连接失败: {response.code}, {response.message}")
            return False
            
    except Exception as e:
        logger.error(f"阿里云DashScope API测试出错: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始测试阿里云API连接...")
    
    # 测试阿里云语音识别API
    nls_result = test_nls_api()
    
    # 测试阿里云DashScope API
    dashscope_result = test_dashscope_api()
    
    # 输出测试结果
    logger.info("测试结果:")
    logger.info(f"阿里云语音识别API: {'成功' if nls_result else '失败'}")
    logger.info(f"阿里云DashScope API: {'成功' if dashscope_result else '失败'}")
    
    # 返回测试结果
    return nls_result and dashscope_result

if __name__ == "__main__":
    main()
