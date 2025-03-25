from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import uuid

from digital_human.models.tts_model import tts_model
from digital_human.models.face_model import face_model
from digital_human.utils.media_utils import MediaUtils
from digital_human.config.config import DATA_DIR

# 创建临时文件目录
TEMP_DIR = DATA_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# 创建静态文件目录
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# 创建FastAPI应用
app = FastAPI(title="数字人API", description="数字人音视频生成API")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class TTSRequest(BaseModel):
    """文本转语音请求模型"""
    text: str
    speaker: str = "default"
    speed: float = 1.0

class TTSResponse(BaseModel):
    """文本转语音响应模型"""
    audio_url: str
    video_url: str
    duration: float
    sample_rate: int

@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """文本转语音并生成口型同步视频"""
    try:
        # 生成唯一文件名
        audio_filename = f"tts_{uuid.uuid4()}.wav"
        video_filename = f"tts_{uuid.uuid4()}.mp4"
        
        audio_path = TEMP_DIR / audio_filename
        video_path = TEMP_DIR / video_filename
        
        # 生成语音
        speech, sample_rate = tts_model.generate_speech(
            request.text, 
            output_path=str(audio_path),
            speaker=request.speaker,
            speed=request.speed
        )
        
        # 生成口型同步视频
        frames, fps = face_model.generate_talking_video(
            str(audio_path),
            request.text  # 传入文本用于生成 Viseme 序列
        )
        
        # 保存视频
        MediaUtils.save_video(frames, fps, str(video_path), with_audio=str(audio_path))
        
        # 检查文件是否成功生成
        if not video_path.exists():
            raise HTTPException(status_code=500, detail="视频生成失败")
            
        return {
            "audio_url": f"/api/files/{audio_filename}",
            "video_url": f"/api/files/{video_filename}",
            "duration": len(speech) / sample_rate,
            "sample_rate": sample_rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tts/speakers")
async def get_available_speakers():
    """获取可用的说话人列表"""
    try:
        speakers = tts_model.get_available_speakers()
        return {"speakers": speakers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_face")
async def upload_face(file: UploadFile = File(...)):
    """上传人脸图片"""
    try:
        # 保存上传的文件
        face_path = STATIC_DIR / "face.jpg"
        with open(face_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 加载人脸图像
        face_model.load_face_image(str(face_path))
        
        # 生成新的空闲视频
        frames, fps = face_model.generate_idle_video(duration_seconds=5)
        idle_video_path = STATIC_DIR / "idle.mp4"
        MediaUtils.save_video(frames, fps, str(idle_video_path))
        
        return {"message": "上传成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{filename}")
async def get_file(filename: str):
    """获取生成的文件"""
    file_path = TEMP_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(file_path))

@app.get("/")
async def root():
    """返回主页"""
    return FileResponse(STATIC_DIR / "index.html")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理操作"""
    try:
        # 清理临时文件
        for file in TEMP_DIR.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                print(f"清理临时文件失败: {str(e)}")
    except Exception as e:
        print(f"清理操作失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 