import sys
import os
import logging
import json
import shutil
import uuid
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
# 添加audio-text模块路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../audio-text")))

# 指定.env文件路径并加载环境变量
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../audio-text/.env"))
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"已加载环境变量文件: {env_path}")
else:
    # 尝试加载python-backend目录下的.env文件
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"已加载环境变量文件: {env_path}")
    else:
        # 尝试加载项目根目录下的.env文件
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"已加载环境变量文件: {env_path}")
        else:
            print("警告: 未找到.env文件，环境变量可能未正确加载")

# 导入配置
from config import OUTPUT_DIR, UPLOADS_DIR

# 创建线程池执行器
thread_pool = ThreadPoolExecutor(max_workers=4)

# 创建任务跟踪系统
background_tasks = {}

# 导入音频处理模块
from audio_processing.speech_to_text import SpeechToText
from text_processing.segmenter import TextSegmenter
from text_processing.tagger import TextTagger
from ai_generation.content_creator import ContentCreator

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('api')

# 创建FastAPI应用
app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许前端开发服务器的域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 headers
)

# 输出和上传目录
output_dir = OUTPUT_DIR
uploads_dir = UPLOADS_DIR

# 存储任务信息的字典
jobs: Dict[str, Dict[str, Any]] = {}

# Create necessary directories
os.makedirs(output_dir, exist_ok=True)
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

@app.put("/api/jobs/{job_id}/update-original-text")
async def update_original_text(job_id: str, request: Request):
    """更新任务的原始文本"""
    try:
        # 检查任务是否存在
        job_folder = os.path.join(output_dir, job_id)
        if not os.path.exists(job_folder):
            raise HTTPException(status_code=404, detail="任务不存在")
            
        # 获取请求体
        body = await request.json()
        new_text = body.get("text")
        
        if not new_text:
            raise HTTPException(status_code=400, detail="缺少文本内容")
            
        # 更新转写结果文件
        transcript_file = os.path.join(job_folder, "transcript.txt")
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(new_text)
            
        # 更新脚本文件中的原始文本
        scripts_file = os.path.join(job_folder, "scripts.json")
        if os.path.exists(scripts_file):
            try:
                with open(scripts_file, "r", encoding="utf-8") as f:
                    scripts = json.load(f)
                    
                # 更新原始文本
                if isinstance(scripts, list):
                    # 如果是旧格式，转换为新格式
                    scripts = {
                        "original_text": new_text,
                        "scripts": scripts
                    }
                else:
                    # 更新现有格式
                    scripts["original_text"] = new_text
                    
                # 保存更新后的脚本
                with open(scripts_file, "w", encoding="utf-8") as f:
                    json.dump(scripts, f, ensure_ascii=False)
            except Exception as e:
                logging.error(f"更新脚本文件中的原始文本时出错: {str(e)}")
                # 继续执行，不因为脚本文件更新失败而中断
        
        return {
            "job_id": job_id,
            "message": "原始文本已更新"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"更新原始文本时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

# 添加后台任务处理函数
def run_in_background(func, *args, **kwargs):
    """在后台线程中运行函数"""
    task_id = str(uuid.uuid4())
    task_name = func.__name__
    
    # 创建任务记录
    background_tasks[task_id] = {
        "id": task_id,
        "name": task_name,
        "status": "pending",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "args": str(args),
        "kwargs": str(kwargs),
        "result": None,
        "error": None
    }
    
    def task_wrapper(*args, **kwargs):
        try:
            # 更新状态为运行中
            background_tasks[task_id]["status"] = "running"
            
            # 执行任务
            result = func(*args, **kwargs)
            
            # 更新状态为完成
            background_tasks[task_id]["status"] = "completed"
            background_tasks[task_id]["end_time"] = datetime.now().isoformat()
            background_tasks[task_id]["result"] = "成功完成"
            
            return result
        except Exception as e:
            # 更新状态为错误
            background_tasks[task_id]["status"] = "error"
            background_tasks[task_id]["end_time"] = datetime.now().isoformat()
            background_tasks[task_id]["error"] = str(e)
            
            # 重新抛出异常
            raise
    
    # 提交任务到线程池
    future = thread_pool.submit(task_wrapper, *args, **kwargs)
    
    # 清理已完成的任务（保留最近50个任务）
    if len(background_tasks) > 50:
        # 找出最早的已完成任务
        completed_tasks = [
            (task_id, task) for task_id, task in background_tasks.items()
            if task["status"] in ["completed", "error"] and task["end_time"] is not None
        ]
        
        # 按结束时间排序
        completed_tasks.sort(key=lambda x: x[1]["end_time"])
        
        # 删除最早的任务，直到总数不超过50
        for old_task_id, _ in completed_tasks[:len(background_tasks) - 50]:
            del background_tasks[old_task_id]
    
    return future, task_id

# 同步版本的脚本生成函数
def generate_scripts_for_job_sync(job_id: str, num_scripts: int, custom_prompt: str = None, overwrite: bool = False):
    """为指定任务生成脚本（同步版本）"""
    try:
        job_folder = os.path.join(output_dir, job_id)
        status_file = os.path.join(job_folder, "status.json")
        transcript_file = os.path.join(job_folder, "transcript.txt")
        tags_file = os.path.join(job_folder, "tags.json")
        scripts_file = os.path.join(job_folder, "scripts.json")
        
        logging.info(f"开始生成脚本: {job_id}")
        
        # 读取转写结果
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript = f.read()
            
        # 读取标签（如果存在）
        tags = []
        if os.path.exists(tags_file):
            try:
                with open(tags_file, "r", encoding="utf-8") as f:
                    tags = json.load(f)
            except Exception as e:
                logging.warning(f"读取标签文件失败: {str(e)}")
        
        # 创建脚本生成对象
        logging.info("创建脚本生成对象")
        content_creator = ContentCreator()
        
        # 开始生成脚本
        logging.info("开始生成脚本")
        try:
            new_scripts = content_creator.generate_multiple_scripts(
                transcript, 
                tags=tags, 
                num_scripts=num_scripts,
                custom_prompt=custom_prompt
            )
        except Exception as e:
            import traceback
            logging.error(f"生成脚本过程中出错: {str(e)}")
            logging.error(f"错误详情: {traceback.format_exc()}")
            raise
        
        # 检查生成结果
        if new_scripts is None:
            raise ValueError("生成结果为空")
            
        logging.info(f"生成脚本完成，结果长度: {len(new_scripts) if new_scripts else 0}")
        
        # 处理现有脚本（如果存在）
        existing_scripts = None
        original_format = None
        if os.path.exists(scripts_file):
            try:
                with open(scripts_file, "r", encoding="utf-8") as f:
                    existing_scripts = json.load(f)
                    
                # 确定原始格式
                if isinstance(existing_scripts, list):
                    original_format = "array"
                elif isinstance(existing_scripts, dict) and "scripts" in existing_scripts:
                    original_format = "object_with_scripts"
                elif isinstance(existing_scripts, dict):
                    original_format = "object"
            except Exception as e:
                logging.warning(f"读取现有脚本文件失败: {str(e)}")
        
        if overwrite:
            # 覆盖模式：使用新生成的脚本，但保持原始格式
            logging.info("使用覆盖模式，替换现有脚本")
            if original_format == "object_with_scripts":
                # 如果原始格式是包含scripts字段的对象
                if isinstance(existing_scripts, dict):
                    # 保留原始对象的其他字段
                    combined_scripts = existing_scripts.copy()
                    combined_scripts["scripts"] = new_scripts
                    # 确保有原文
                    combined_scripts["original_text"] = transcript
                else:
                    combined_scripts = {"scripts": new_scripts, "original_text": transcript}
            elif original_format == "object":
                # 如果原始格式是其他类型的对象
                combined_scripts = {"scripts": new_scripts, "original_text": transcript}
            else:
                # 默认使用对象格式，即使原始格式是数组或没有原始格式
                combined_scripts = {"scripts": new_scripts, "original_text": transcript}
        else:
            # 追加模式：读取现有脚本并追加
            logging.info("使用追加模式，保留现有脚本")
            # 读取现有脚本（如果存在）
            existing_scripts = []
            if os.path.exists(scripts_file):
                try:
                    with open(scripts_file, "r", encoding="utf-8") as f:
                        existing_scripts = json.load(f)
                except Exception as e:
                    logging.warning(f"读取现有脚本文件失败，将创建新文件: {str(e)}")
            
            # 合并脚本
            if isinstance(existing_scripts, list):
                # 如果现有脚本是数组，直接追加
                combined_scripts = {"scripts": existing_scripts + new_scripts, "original_text": transcript}
            elif isinstance(existing_scripts, dict) and "scripts" in existing_scripts:
                # 如果现有脚本是包含scripts数组的对象
                combined_scripts = existing_scripts.copy()
                combined_scripts["scripts"] = combined_scripts["scripts"] + new_scripts
                # 确保有原文
                combined_scripts["original_text"] = transcript
            else:
                # 如果没有现有脚本或格式不正确，使用新脚本并包装成对象格式
                combined_scripts = {"scripts": new_scripts, "original_text": transcript}
        
        # 保存生成结果
        with open(scripts_file, "w", encoding="utf-8") as f:
            json.dump(combined_scripts, f, ensure_ascii=False)
            
        # 更新状态为完成
        with open(status_file, "w") as f:
            json.dump({
                "status": "completed",
                "filename": os.path.basename(transcript_file).replace(f"{job_id}_", ""),
                "message": "脚本生成完成",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }, f)
            
        return combined_scripts
            
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
        raise

# 异步版本的脚本生成函数
async def generate_scripts_for_job(job_id: str, num_scripts: int, custom_prompt: str = None, overwrite: bool = False):
    """为指定任务生成脚本（异步版本）"""
    # 在后台线程中运行同步函数
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        generate_scripts_for_job_sync,
        job_id,
        num_scripts,
        custom_prompt,
        overwrite
    )

@app.post("/api/jobs/{job_id}/generate-scripts")
async def generate_scripts_api(
    job_id: str, 
    num_scripts: int = 5, 
    custom_prompt: str = None,
    overwrite: bool = False
):
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
            
        # 在后台线程中生成脚本
        future, task_id = run_in_background(generate_scripts_for_job_sync, job_id, num_scripts, custom_prompt, overwrite)
        
        return {
            "job_id": job_id,
            "task_id": task_id,
            "status": "processing",
            "message": f"正在生成 {num_scripts} 份脚本"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"生成脚本时出错: {str(e)}")
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

@app.get("/api/status")
async def get_api_status():
    """获取API服务状态"""
    try:
        # 读取状态文件
        status_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio-text", "status.json")
        if not os.path.exists(status_file):
            return {
                "nlsApi": {"status": "offline", "message": "状态文件不存在"},
                "dashscopeApi": {"status": "offline", "message": "状态文件不存在"},
                "lastCheck": datetime.now().isoformat()
            }
            
        with open(status_file, "r", encoding="utf-8") as f:
            status = json.load(f)
            
        return status
    except Exception as e:
        logging.error(f"获取API状态时出错: {str(e)}")
        return {
            "nlsApi": {"status": "error", "message": f"获取状态时出错: {str(e)}"},
            "dashscopeApi": {"status": "error", "message": f"获取状态时出错: {str(e)}"},
            "lastCheck": datetime.now().isoformat()
        }

@app.get("/api/system/tasks")
async def get_background_tasks():
    """获取所有后台任务的状态"""
    # 按开始时间倒序排序
    sorted_tasks = sorted(
        background_tasks.values(),
        key=lambda x: x["start_time"],
        reverse=True
    )
    return {"tasks": sorted_tasks}

@app.get("/api/system/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取指定后台任务的状态"""
    if task_id not in background_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return background_tasks[task_id]

@app.get("/api/system/status")
async def get_system_status():
    """获取系统状态"""
    # 计算活跃任务数量
    active_tasks = sum(1 for task in background_tasks.values() if task["status"] in ["pending", "running"])
    
    # 计算线程池状态
    thread_stats = {
        "max_workers": thread_pool._max_workers,
        "active_threads": len([t for t in thread_pool._threads if t is not None and t.is_alive()]),
        "tasks_completed": thread_pool._work_queue.qsize()
    }
    
    # 获取最近的任务
    recent_tasks = sorted(
        background_tasks.values(),
        key=lambda x: x["start_time"],
        reverse=True
    )[:10]  # 只返回最近10个任务
    
    return {
        "active_tasks": active_tasks,
        "total_tasks": len(background_tasks),
        "thread_pool": thread_stats,
        "recent_tasks": recent_tasks
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
