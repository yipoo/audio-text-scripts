import sys
import os
import logging
import json
import shutil
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加复制后的 audio-text 目录到 Python 路径
audio_text_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../audio-text"))
if os.path.exists(audio_text_dir):
    sys.path.append(audio_text_dir)
    print(f"Added audio-text project: {audio_text_dir} to Python path")

# 加载环境变量
try:
    from dotenv import load_dotenv
    # 尝试加载 audio-text 目录下的 .env 文件
    env_path = os.path.join(audio_text_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        print(f"Warning: .env file not found at {env_path}")
except ImportError:
    print("Warning: python-dotenv not installed, environment variables may not be loaded correctly")

# 尝试从 audio-text 项目导入模块
try:
    from audio_processing.speech_to_text import SpeechToText
    from text_processing.segmenter import TextSegmenter
    from text_processing.tagger import TextTagger
    from ai_generation.content_creator import ContentCreator
    print("Successfully imported SpeechToText, TextSegmenter, TextTagger, ContentCreator from audio-text project")
except ImportError as e:
    print(f"Error importing SpeechToText, TextSegmenter, TextTagger, ContentCreator from audio-text project: {e}")

# 存储任务信息的字典
jobs: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="Short Video Marketing API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许前端开发服务器的域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 headers
)

# Create necessary directories
output_dir = os.path.join(os.path.dirname(__file__), "../output")
os.makedirs(output_dir, exist_ok=True)

uploads_dir = os.path.join(os.path.dirname(__file__), "../uploads")
os.makedirs(uploads_dir, exist_ok=True)

# API Routes
@app.get("/")
async def root():
    return {"message": "API 服务正常运行"}

@app.post("/api/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """上传音频文件并开始处理"""
    try:
        # 生成唯一的任务ID
        job_id = str(uuid.uuid4())
        
        # 创建任务目录
        job_folder = os.path.join(output_dir, job_id)
        os.makedirs(job_folder, exist_ok=True)
        
        # 保存上传的文件
        file_path = os.path.join(uploads_dir, f"{job_id}_{file.filename}")
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
            
        # 创建并保存任务状态
        status = {
            "status": "processing",
            "filename": file.filename,
            "message": "文件已上传，开始处理",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        with open(os.path.join(job_folder, "status.json"), "w") as f:
            json.dump(status, f, ensure_ascii=False)
            
        # 在后台开始处理音频文件
        background_tasks.add_task(process_audio_file, job_id, file_path)
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "文件已上传，开始处理"
        }
        
    except Exception as e:
        logging.error(f"上传文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
async def list_jobs():
    """获取所有任务的列表"""
    try:
        jobs = []
        for job_id in os.listdir(output_dir):
            status_file = os.path.join(output_dir, job_id, "status.json")
            if os.path.exists(status_file):
                with open(status_file, "r") as f:
                    status = json.load(f)
                    status["job_id"] = job_id
                    jobs.append(status)
        return jobs
    except Exception as e:
        logging.error(f"获取任务列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """获取指定任务的状态"""
    try:
        status_file = os.path.join(output_dir, job_id, "status.json")
        if not os.path.exists(status_file):
            raise HTTPException(status_code=404, detail="任务不存在")
            
        with open(status_file, "r") as f:
            status = json.load(f)
            status["job_id"] = job_id
            return status
            
    except Exception as e:
        logging.error(f"获取任务状态时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/retry")
async def retry_job(job_id: str, background_tasks: BackgroundTasks):
    """重试失败的任务"""
    try:
        # 检查任务是否存在
        job_folder = os.path.join(output_dir, job_id)
        status_file = os.path.join(job_folder, "status.json")
        transcript_file = os.path.join(job_folder, "transcript.txt")
        
        if not os.path.exists(status_file):
            raise HTTPException(status_code=404, detail="任务不存在")
            
        # 读取当前状态
        with open(status_file, "r") as f:
            status = json.load(f)
            
        # 检查任务是否处于错误状态
        if status["status"] != "error":
            raise HTTPException(status_code=400, detail=f"只能重试失败的任务，当前状态: {status['status']}")
        
        # 更新状态为处理中
        status["status"] = "processing"
        status["message"] = "正在重新处理"
        status["updated_at"] = datetime.now().isoformat()
        
        with open(status_file, "w") as f:
            json.dump(status, f, ensure_ascii=False)
        
        # 检查是否已有转写结果
        if os.path.exists(transcript_file) and os.path.getsize(transcript_file) > 0:
            # 如果已有转写结果，只重新生成标签和脚本
            logging.info(f"找到转写结果，只重新生成标签和脚本: {job_id}")
            
            # 读取转写结果
            with open(transcript_file, "r", encoding="utf-8") as f:
                transcript = f.read()
                
            # 在后台生成标签和脚本
            background_tasks.add_task(generate_tags_and_scripts_for_job, job_id, transcript)
            
            return {
                "job_id": job_id,
                "status": "processing",
                "message": "正在重新生成标签和脚本"
            }
        else:
            # 如果没有转写结果，尝试从音频文件开始重新处理
            logging.info(f"未找到转写结果，尝试从音频文件重新处理: {job_id}")
            
            # 尝试在uploads_dir中查找原始音频文件
            original_filename = status.get("filename", "")
            file_path = os.path.join(uploads_dir, f"{job_id}_{original_filename}")
            
            if os.path.exists(file_path):
                # 在后台重新处理音频文件
                background_tasks.add_task(process_audio_file, job_id, file_path)
                
                return {
                    "job_id": job_id,
                    "status": "processing",
                    "message": "正在重新处理音频文件"
                }
            else:
                raise HTTPException(status_code=404, detail="找不到原始音频文件，无法重新处理")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"重试任务时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_tags_and_scripts_for_job(job_id: str, transcript: str):
    """为指定任务生成标签和脚本"""
    try:
        job_folder = os.path.join(output_dir, job_id)
        status_file = os.path.join(job_folder, "status.json")
        transcript_file = os.path.join(job_folder, "transcript.txt")
        tags_file = os.path.join(job_folder, "tags.json")
        scripts_file = os.path.join(job_folder, "scripts.json")
        
        logging.info(f"开始生成标签和脚本: {job_id}")
        
        # 创建标签生成对象
        logging.info("创建标签生成对象")
        tagger = TextTagger(topK=10)
        
        # 开始生成标签
        logging.info("开始生成标签")
        try:
            tags = tagger.extract_tags(transcript)
        except Exception as e:
            import traceback
            logging.error(f"生成标签过程中出错: {str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
            raise
        
        # 检查生成结果
        if tags is None:
            raise ValueError("生成结果为空")
            
        logging.info(f"生成标签完成，结果长度: {len(tags) if tags else 0}")
        
        # 保存生成结果
        with open(tags_file, "w", encoding="utf-8") as f:
            json.dump(tags, f, ensure_ascii=False)
            
        # 创建脚本生成对象
        logging.info("创建脚本生成对象")
        content_creator = ContentCreator()
        
        # 开始生成脚本
        logging.info("开始生成脚本")
        try:
            scripts = content_creator.generate_multiple_scripts(transcript, tags=tags, num_scripts=5)
        except Exception as e:
            import traceback
            logging.error(f"生成脚本过程中出错: {str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
            raise
        
        # 检查生成结果
        if scripts is None:
            raise ValueError("生成结果为空")
            
        logging.info(f"生成脚本完成，结果长度: {len(scripts) if scripts else 0}")
        
        # 保存生成结果
        result = {
            "original_text": transcript,
            "scripts": scripts
        }
        
        with open(scripts_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
            
        # 更新状态为完成
        with open(status_file, "w") as f:
            json.dump({
                "status": "completed",
                "filename": os.path.basename(transcript_file).replace(f"{job_id}_", ""),
                "message": "标签和脚本生成完成",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f)
            
    except Exception as e:
        import traceback
        logging.error(f"生成标签和脚本时出错: {str(e)}")
        logging.error(f"错误详情: {traceback.format_exc()}")
        # 更新状态为错误
        with open(status_file, "w") as f:
            json.dump({
                "status": "error",
                "filename": os.path.basename(transcript_file).replace(f"{job_id}_", ""),
                "message": str(e),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False)

@app.get("/api/jobs/{job_id}/transcript")
async def get_job_transcript(job_id: str):
    """获取指定任务的转写结果"""
    try:
        # 检查任务是否存在
        status_file = os.path.join(output_dir, job_id, "status.json")
        if not os.path.exists(status_file):
            raise HTTPException(status_code=404, detail="任务不存在")
            
        # 读取当前状态
        with open(status_file, "r") as f:
            status = json.load(f)
            
        # 检查任务是否已完成
        if status["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {status['status']}")
            
        # 读取转写结果
        transcript_file = os.path.join(output_dir, job_id, "transcript.txt")
        if not os.path.exists(transcript_file):
            raise HTTPException(status_code=404, detail="转写结果文件不存在")
            
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript = f.read()
            
        if not transcript:
            return {"transcript": "转写结果为空，可能是音频文件没有可识别的语音内容。"}
            
        return {"transcript": transcript}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取转写结果时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}/tags")
async def get_job_tags(job_id: str):
    """获取指定任务的标签"""
    try:
        # 检查任务是否存在
        status_file = os.path.join(output_dir, job_id, "status.json")
        if not os.path.exists(status_file):
            raise HTTPException(status_code=404, detail="任务不存在")
            
        # 读取当前状态
        with open(status_file, "r") as f:
            status = json.load(f)
            
        # 检查任务是否已完成
        if status["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {status['status']}")
            
        # 读取标签
        tags_file = os.path.join(output_dir, job_id, "tags.json")
        if not os.path.exists(tags_file):
            raise HTTPException(status_code=404, detail="标签文件不存在")
            
        with open(tags_file, "r", encoding="utf-8") as f:
            tags = json.load(f)
            
        return {"tags": tags}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取标签时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}/scripts")
async def get_job_scripts(job_id: str):
    """获取指定任务的脚本"""
    try:
        # 检查任务是否存在
        status_file = os.path.join(output_dir, job_id, "status.json")
        if not os.path.exists(status_file):
            raise HTTPException(status_code=404, detail="任务不存在")
            
        # 读取当前状态
        with open(status_file, "r") as f:
            status = json.load(f)
            
        # 检查任务是否已完成
        if status["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {status['status']}")
            
        # 读取脚本
        scripts_file = os.path.join(output_dir, job_id, "scripts.json")
        if not os.path.exists(scripts_file):
            raise HTTPException(status_code=404, detail="脚本文件不存在")
            
        with open(scripts_file, "r", encoding="utf-8") as f:
            scripts = json.load(f)
            
        return {"scripts": scripts}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"获取脚本时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/generate-tags")
async def generate_tags(job_id: str, background_tasks: BackgroundTasks):
    """手动为指定任务生成标签"""
    try:
        # 检查任务是否存在
        status_file = os.path.join(output_dir, job_id, "status.json")
        if not os.path.exists(status_file):
            raise HTTPException(status_code=404, detail="任务不存在")
            
        # 读取当前状态
        with open(status_file, "r") as f:
            status = json.load(f)
            
        # 检查任务是否已完成
        if status["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {status['status']}")
            
        # 读取转写结果
        transcript_file = os.path.join(output_dir, job_id, "transcript.txt")
        if not os.path.exists(transcript_file):
            raise HTTPException(status_code=404, detail="转写结果文件不存在")
            
        # 更新状态为处理中
        status["status"] = "processing"
        status["message"] = "正在生成标签"
        status["updated_at"] = datetime.now().isoformat()
        
        with open(status_file, "w") as f:
            json.dump(status, f, ensure_ascii=False)
            
        # 在后台生成标签
        background_tasks.add_task(generate_tags_for_job, job_id)
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "正在生成标签"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"生成标签时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/generate-scripts")
async def generate_scripts(job_id: str, background_tasks: BackgroundTasks, num_scripts: int = 5):
    """手动为指定任务生成脚本"""
    try:
        # 检查任务是否存在
        status_file = os.path.join(output_dir, job_id, "status.json")
        if not os.path.exists(status_file):
            raise HTTPException(status_code=404, detail="任务不存在")
            
        # 读取当前状态
        with open(status_file, "r") as f:
            status = json.load(f)
            
        # 检查任务是否已完成
        if status["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"任务尚未完成，当前状态: {status['status']}")
            
        # 读取转写结果
        transcript_file = os.path.join(output_dir, job_id, "transcript.txt")
        if not os.path.exists(transcript_file):
            raise HTTPException(status_code=404, detail="转写结果文件不存在")
            
        # 更新状态为处理中
        status["status"] = "processing"
        status["message"] = "正在生成脚本"
        status["updated_at"] = datetime.now().isoformat()
        
        with open(status_file, "w") as f:
            json.dump(status, f, ensure_ascii=False)
            
        # 在后台生成脚本
        background_tasks.add_task(generate_scripts_for_job, job_id, num_scripts)
        
        return {
            "job_id": job_id,
            "status": "processing",
            "message": f"正在生成 {num_scripts} 份脚本"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"生成脚本时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def check_status():
    """检查各项服务的状态"""
    try:
        # 状态文件路径
        status_file = os.path.join(os.path.dirname(__file__), "../audio-text/status.json")
        
        # 运行 test_api.py 脚本
        script_path = os.path.join(os.path.dirname(__file__), "../audio-text/test_api.py")
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), "../audio-text")
        )
        
        stdout, stderr = process.communicate()
        
        # 解析输出并构建状态
        nls_status = {
            "status": "error",
            "message": "未知错误"
        }
        dashscope_status = {
            "status": "error",
            "message": "未知错误"
        }
        
        if process.returncode == 0:
            # 检查 NLS 状态
            if "NLS连接测试成功" in stdout:
                nls_status = {
                    "status": "online",
                    "message": "连接正常"
                }
            elif "成功导入阿里云NLS SDK" in stdout:
                nls_status = {
                    "status": "online",
                    "message": "SDK导入成功"
                }
                
            # 检查 DashScope 状态
            if "阿里云DashScope API连接成功" in stdout:
                dashscope_status = {
                    "status": "online",
                    "message": "连接正常"
                }
            elif "成功导入阿里云DashScope SDK" in stdout:
                dashscope_status = {
                    "status": "online",
                    "message": "SDK导入成功"
                }
        else:
            # 如果脚本执行失败，设置错误消息
            nls_status["message"] = stderr or "执行测试脚本失败"
            dashscope_status["message"] = stderr or "执行测试脚本失败"
        
        # 保存状态到文件
        status = {
            "nlsApi": nls_status,
            "dashscopeApi": dashscope_status,
            "lastCheck": datetime.now().isoformat(),
            "stdout": stdout,
            "stderr": stderr
        }
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
            
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_audio_file(job_id: str, file_path: str):
    """在后台处理音频文件"""
    try:
        job_folder = os.path.join(output_dir, job_id)
        status_file = os.path.join(job_folder, "status.json")
        transcript_file = os.path.join(job_folder, "transcript.txt")
        tags_file = os.path.join(job_folder, "tags.json")
        scripts_file = os.path.join(job_folder, "scripts.json")
        
        logging.info(f"开始处理音频文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
            
        # 创建语音转文字对象
        logging.info("创建语音转文字对象")
        transcriber = SpeechToText()
        
        # 更新状态为转写中
        with open(status_file, "w") as f:
            json.dump({
                "status": "processing",
                "filename": os.path.basename(file_path).replace(f"{job_id}_", ""),
                "message": "正在转写音频",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False)
        
        # 开始转写 - 注意：transcribe_file 返回 (transcript, output_file)
        logging.info("开始转写音频")
        try:
            transcript_result = transcriber.transcribe_file(file_path, transcript_file)
            # 检查返回值类型
            if isinstance(transcript_result, tuple) and len(transcript_result) == 2:
                transcript, _ = transcript_result
            else:
                # 如果不是元组，可能是直接返回了转写结果
                transcript = transcript_result
                logging.warning("transcribe_file 没有返回预期的元组，使用单一返回值作为转写结果")
        except Exception as e:
            import traceback
            logging.error(f"转写过程中出错: {str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
            raise
        
        # 检查转写结果
        if transcript is None:
            raise ValueError("转写结果为空")
            
        logging.info(f"转写完成，结果长度: {len(transcript) if transcript else 0}")
        
        # 更新状态为生成标签中
        with open(status_file, "w") as f:
            json.dump({
                "status": "processing",
                "filename": os.path.basename(file_path).replace(f"{job_id}_", ""),
                "message": "正在生成标签",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False)
        
        # 生成标签
        logging.info("开始生成标签")
        try:
            tagger = TextTagger(topK=10)
            tags = tagger.extract_tags(transcript)
            
            # 保存标签
            with open(tags_file, "w", encoding="utf-8") as f:
                json.dump(tags, f, ensure_ascii=False)
                
            logging.info(f"标签生成完成，共 {len(tags)} 个标签")
        except Exception as e:
            import traceback
            logging.error(f"生成标签过程中出错: {str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
            # 继续执行，不中断流程
        
        # 更新状态为生成脚本中
        with open(status_file, "w") as f:
            json.dump({
                "status": "processing",
                "filename": os.path.basename(file_path).replace(f"{job_id}_", ""),
                "message": "正在生成脚本",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False)
        
        # 生成脚本
        logging.info("开始生成脚本")
        try:
            creator = ContentCreator()
            scripts = creator.generate_multiple_scripts(transcript, tags=tags, num_scripts=5)
            
            # 保存脚本
            result = {
                "original_text": transcript,
                "scripts": scripts
            }
            
            with open(scripts_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False)
                
            logging.info(f"脚本生成完成，共 {len(scripts)} 份脚本")
        except Exception as e:
            import traceback
            logging.error(f"生成脚本过程中出错: {str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
            # 继续执行，不中断流程
        
        # 更新状态为完成
        with open(status_file, "w") as f:
            json.dump({
                "status": "completed",
                "filename": os.path.basename(file_path).replace(f"{job_id}_", ""),
                "message": "处理完成",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False)
            
    except Exception as e:
        import traceback
        logging.error(f"处理音频文件时出错: {str(e)}")
        logging.error(f"错误详情: {traceback.format_exc()}")
        # 更新状态为错误
        with open(status_file, "w") as f:
            json.dump({
                "status": "error",
                "filename": os.path.basename(file_path).replace(f"{job_id}_", ""),
                "message": str(e),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False)

async def generate_tags_for_job(job_id: str):
    """为指定任务生成标签"""
    try:
        job_folder = os.path.join(output_dir, job_id)
        status_file = os.path.join(job_folder, "status.json")
        transcript_file = os.path.join(job_folder, "transcript.txt")
        tags_file = os.path.join(job_folder, "tags.json")
        
        logging.info(f"开始生成标签: {job_id}")
        
        # 检查文件是否存在
        if not os.path.exists(transcript_file):
            raise FileNotFoundError(f"转写结果文件不存在: {transcript_file}")
            
        # 读取转写结果
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript = f.read()
            
        # 创建标签生成对象
        logging.info("创建标签生成对象")
        tagger = TextTagger(topK=10)
        
        # 开始生成标签
        logging.info("开始生成标签")
        try:
            tags = tagger.extract_tags(transcript)
        except Exception as e:
            import traceback
            logging.error(f"生成标签过程中出错: {str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
            raise
        
        # 检查生成结果
        if tags is None:
            raise ValueError("生成结果为空")
            
        logging.info(f"生成标签完成，结果长度: {len(tags) if tags else 0}")
        
        # 保存生成结果
        with open(tags_file, "w", encoding="utf-8") as f:
            json.dump(tags, f, ensure_ascii=False)
            
        # 更新状态为完成
        with open(status_file, "w") as f:
            json.dump({
                "status": "completed",
                "filename": os.path.basename(transcript_file).replace(f"{job_id}_", ""),
                "message": "标签生成完成",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f)
            
    except Exception as e:
        import traceback
        logging.error(f"生成标签时出错: {str(e)}")
        logging.error(f"错误详情: {traceback.format_exc()}")
        # 更新状态为错误
        with open(status_file, "w") as f:
            json.dump({
                "status": "error",
                "filename": os.path.basename(transcript_file).replace(f"{job_id}_", ""),
                "message": str(e),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False)

async def generate_scripts_for_job(job_id: str, num_scripts: int):
    """为指定任务生成脚本"""
    try:
        job_folder = os.path.join(output_dir, job_id)
        status_file = os.path.join(job_folder, "status.json")
        transcript_file = os.path.join(job_folder, "transcript.txt")
        tags_file = os.path.join(job_folder, "tags.json")
        scripts_file = os.path.join(job_folder, "scripts.json")
        
        logging.info(f"开始生成脚本: {job_id}")
        
        # 检查文件是否存在
        if not os.path.exists(transcript_file):
            raise FileNotFoundError(f"转写结果文件不存在: {transcript_file}")
            
        # 读取转写结果
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript = f.read()
            
        # 读取标签
        with open(tags_file, "r", encoding="utf-8") as f:
            tags = json.load(f)
            
        # 创建脚本生成对象
        logging.info("创建脚本生成对象")
        content_creator = ContentCreator()
        
        # 开始生成脚本
        logging.info("开始生成脚本")
        try:
            scripts = content_creator.generate_multiple_scripts(transcript, tags=tags, num_scripts=num_scripts)
        except Exception as e:
            import traceback
            logging.error(f"生成脚本过程中出错: {str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
            raise
        
        # 检查生成结果
        if scripts is None:
            raise ValueError("生成结果为空")
            
        logging.info(f"生成脚本完成，结果长度: {len(scripts) if scripts else 0}")
        
        # 保存生成结果
        with open(scripts_file, "w", encoding="utf-8") as f:
            json.dump(scripts, f, ensure_ascii=False)
            
        # 更新状态为完成
        with open(status_file, "w") as f:
            json.dump({
                "status": "completed",
                "filename": os.path.basename(transcript_file).replace(f"{job_id}_", ""),
                "message": "脚本生成完成",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f)
            
    except Exception as e:
        import traceback
        logging.error(f"生成脚本时出错: {str(e)}")
        logging.error(f"错误详情: {traceback.format_exc()}")
        # 更新状态为错误
        with open(status_file, "w") as f:
            json.dump({
                "status": "error",
                "filename": os.path.basename(transcript_file).replace(f"{job_id}_", ""),
                "message": str(e),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
