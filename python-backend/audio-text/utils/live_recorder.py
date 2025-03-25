from playwright.async_api import async_playwright
import subprocess
import os
import time
import re
import json
import threading
from datetime import datetime

class LiveStreamRecorder:
    def __init__(self):
        self.recording_processes = {}  # 存储正在运行的录制进程
        self.recording_info = {}  # 存储录制相关信息

    async def get_douyin_stream_url(self, douyin_live_url: str):
        """
        获取抖音直播流URL和主播信息
        
        Args:
            douyin_live_url: 抖音直播链接
            
        Returns:
            tuple: (stream_url, streamer_name) 直播流URL和主播名称
        """
        streamer_name = "unknown"
        self._stream_url = None  # 使用实例变量存储stream_url
        print(f"开始获取直播流地址: {douyin_live_url}")
        
        async with async_playwright() as p:
            browser = None
            try:
                # 使用无头模式启动浏览器
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
                )
                print("浏览器已启动")
                
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                page = await context.new_page()
                print("浏览器页面已创建")
                
                # 访问抖音直播页面
                print(f"正在访问直播页面: {douyin_live_url}")
                await page.goto(douyin_live_url, wait_until="networkidle", timeout=60000)
                print("页面已加载完成")
                
                # 等待页面加载
                await page.wait_for_timeout(5000)
                
                # 尝试获取主播名称
                try:
                    print("尝试获取主播名称")
                    # 尝试多个选择器
                    selectors = [
                        '//span[contains(@class, "yEUQAMVJ")]',
                        '//span[contains(@class, "userName")]',
                        '//span[contains(@class, "name")]'
                    ]
                    
                    for selector in selectors:
                        element = await page.query_selector(selector)
                        if element:
                            streamer_name = await element.text_content()
                            streamer_name = streamer_name.strip()
                            print(f"通过选择器 {selector} 找到主播名称: {streamer_name}")
                            break
                    
                    # 如果选择器都失效，尝试从标题获取
                    if not streamer_name or streamer_name == "unknown":
                        title = await page.title()
                        print(f"页面标题: {title}")
                        match = re.search(r'(.+?)的直播间', title)
                        if match:
                            streamer_name = match.group(1).strip()
                            print(f"从标题中提取到主播名称: {streamer_name}")
                except Exception as e:
                    print(f"获取主播名称失败: {e}")
                
                # 监听网络请求
                def set_stream_url(url):
                    self._stream_url = url
                    print(f"设置流地址: {url}")
                
                async def handle_response(response):
                    try:
                        url = response.url
                        if '.flv' in url or '.m3u8' in url:
                            set_stream_url(url)
                            print(f"从响应中捕获到直播流URL: {url}")
                            
                        # 检查WebcastRealtimeInfo API响应
                        if 'webcast/realtimeinfo' in url:
                            try:
                                data = await response.json()
                                if data and 'data' in data and 'live_core_sdk_data' in data['data']:
                                    sdk_data = json.loads(data['data']['live_core_sdk_data']['pull_data'])
                                    if 'stream_data' in sdk_data and sdk_data['stream_data']:
                                        stream_data = json.loads(sdk_data['stream_data'])
                                        if 'data' in stream_data and 'origin' in stream_data['data']:
                                            for item in stream_data['data']['origin']:
                                                if 'flv' in item and item['flv']:
                                                    set_stream_url(item['flv'])
                                                    print(f"从API响应中捕获到直播流URL: {item['flv']}")
                            except Exception as e:
                                print(f"处理API响应时发生错误: {e}")
                    except Exception as e:
                        print(f"处理网络响应时发生错误: {e}")
                
                page.on("response", handle_response)
                
                # 等待一段时间以捕获网络请求
                await page.wait_for_timeout(10000)
                
                # 如果通过网络请求没有获取到流地址，尝试从页面内容中提取
                if not self._stream_url:
                    print("尝试从页面内容中提取直播流地址")
                    page_content = await page.content()
                    
                    # 尝试从页面内容中查找直播流地址
                    flv_match = re.search(r'(https?://[^"\']+\.flv[^"\']*)', page_content)
                    m3u8_match = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', page_content)
                    
                    if flv_match:
                        self._stream_url = flv_match.group(1)
                        print(f"从页面内容中找到FLV流地址: {self._stream_url}")
                    elif m3u8_match:
                        self._stream_url = m3u8_match.group(1)
                        print(f"从页面内容中找到M3U8流地址: {self._stream_url}")
                
                # 如果还是没有找到流地址，尝试执行JavaScript来获取
                if not self._stream_url:
                    print("尝试通过JavaScript获取直播流地址")
                    try:
                        js_result = await page.evaluate('''() => {
                            const videoElement = document.querySelector('video');
                            return videoElement ? videoElement.src : null;
                        }''')
                        if js_result:
                            self._stream_url = js_result
                            print(f"通过JavaScript找到流地址: {self._stream_url}")
                    except Exception as e:
                        print(f"JavaScript获取流地址失败: {e}")
                
                # 尝试从页面变量中获取
                if not self._stream_url:
                    try:
                        js_result = await page.evaluate('''() => {
                            try {
                                const streamData = window.RENDER_DATA?.initialState?.roomStore?.roomInfo?.room?.stream_url;
                                if (streamData?.flv_pull_url) {
                                    return streamData.flv_pull_url.FULL_HD1 || 
                                           streamData.flv_pull_url.HD1 || 
                                           streamData.flv_pull_url.SD1;
                                }
                                return null;
                            } catch (e) {
                                console.error("获取流地址失败:", e);
                                return null;
                            }
                        }''')
                        if js_result:
                            self._stream_url = js_result
                            print(f"从页面变量中获取到流地址: {self._stream_url}")
                    except Exception as e:
                        print(f"从页面变量获取流地址失败: {e}")
                
            except Exception as e:
                print(f"获取直播流地址时发生错误: {e}")
                if browser:
                    await browser.close()
                return None, streamer_name
            finally:
                if browser:
                    try:
                        await browser.close()
                        print("浏览器已关闭")
                    except Exception as e:
                        print(f"关闭浏览器时发生错误: {e}")
        
        if not self._stream_url:
            print("未能获取到直播流地址")
            return None, streamer_name
            
        print(f"成功获取直播流信息 - 流地址: {self._stream_url}, 主播: {streamer_name}")
        return self._stream_url, streamer_name

    def record_stream(self, stream_url, streamer_name="unknown", duration_minutes=None, segment_duration=60, base_output_dir=None):
        """
        使用ffmpeg分段录制直播流
        
        Args:
            stream_url: 直播流URL
            streamer_name: 主播名称，用于创建保存目录
            duration_minutes: 总录制时间(分钟)，None表示持续录制直到手动停止
            segment_duration: 每个片段的时长(秒)
            base_output_dir: 基础输出目录，默认为None表示使用项目根目录下的douyin文件夹
            
        Returns:
            str: 录制任务ID
        """
        if not stream_url:
            print("未获取到直播流地址")
            return None
        
        # 生成任务ID
        task_id = f"rec_{int(time.time())}_{streamer_name}"
        
        # 规范化主播名称，去除非法字符
        safe_streamer_name = re.sub(r'[\\/*?:"<>|]', "_", streamer_name)
        
        # 创建基于主播名称的保存目录
        if base_output_dir is None:
            # 默认使用项目根目录下的douyin文件夹
            base_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../douyin"))
        
        output_dir = os.path.join(base_output_dir, safe_streamer_name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 生成时间戳作为文件名前缀
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_pattern = f"{output_dir}/{timestamp}_%03d.mp3"
        
        # 构建ffmpeg命令
        cmd = [
            "ffmpeg",
            "-i", stream_url,
            "-f", "segment",
            "-segment_time", str(segment_duration),
            "-c:a", "libmp3lame",
            "-q:a", "4",
            "-vn"  # 不包含视频
        ]
        
        # 设置录制总时长限制
        if duration_minutes:
            cmd.extend(["-t", str(duration_minutes * 60)])
            
        cmd.append(output_pattern)
        
        print(f"开始录制直播流: {stream_url}")
        print(f"主播: {streamer_name}")
        print(f"文件将保存在: {output_dir}")
        print(f"每段时长: {segment_duration}秒")
        if duration_minutes:
            print(f"总录制时长: {duration_minutes}分钟")
        else:
            print("将持续录制直到手动停止")
        
        try:
            # 执行ffmpeg命令
            process = subprocess.Popen(cmd)
            
            # 存储进程和录制信息
            self.recording_processes[task_id] = process
            self.recording_info[task_id] = {
                "streamer_name": streamer_name,
                "start_time": datetime.now().isoformat(),
                "output_dir": output_dir,
                "stream_url": stream_url,
                "duration_minutes": duration_minutes,
                "segment_duration": segment_duration,
                "status": "recording"
            }
            
            # 如果设置了录制时长，启动一个线程来等待并终止进程
            if duration_minutes:
                def terminate_after_duration():
                    try:
                        # 等待指定时间
                        time.sleep(duration_minutes * 60)
                        if task_id in self.recording_processes:
                            process = self.recording_processes[task_id]
                            if process.poll() is None:  # 检查进程是否仍在运行
                                process.terminate()
                                if task_id in self.recording_info:
                                    self.recording_info[task_id]["status"] = "completed"
                    except Exception as e:
                        print(f"终止录制时出错: {e}")
                
                threading.Thread(target=terminate_after_duration, daemon=True).start()
            
            return task_id
        except Exception as e:
            print(f"录制过程中出错: {e}")
            return None

    def stop_recording(self, task_id):
        """停止指定的录制任务"""
        if task_id in self.recording_processes:
            process = self.recording_processes[task_id]
            if process.poll() is None:  # 检查进程是否仍在运行
                process.terminate()
                if task_id in self.recording_info:
                    self.recording_info[task_id]["status"] = "stopped"
                    self.recording_info[task_id]["end_time"] = datetime.now().isoformat()
                return True
        return False

    def get_recording_status(self, task_id=None):
        """获取录制任务状态"""
        if task_id:
            if task_id in self.recording_info:
                info = self.recording_info[task_id].copy()
                # 检查进程是否仍在运行
                if task_id in self.recording_processes:
                    process = self.recording_processes[task_id]
                    if process.poll() is not None:  # 进程已结束
                        info["status"] = "completed" if info["status"] == "recording" else info["status"]
                return info
            return None
        else:
            # 返回所有录制任务的状态
            result = {}
            for tid, info in self.recording_info.items():
                result[tid] = info.copy()
                # 检查进程是否仍在运行
                if tid in self.recording_processes:
                    process = self.recording_processes[tid]
                    if process.poll() is not None:  # 进程已结束
                        result[tid]["status"] = "completed" if result[tid]["status"] == "recording" else result[tid]["status"]
            return result

# 创建单例实例
live_recorder = LiveStreamRecorder()

# 示例用法
if __name__ == "__main__":
    douyin_url = "https://live.douyin.com/16583650782"
    stream_url, streamer_name = live_recorder.get_douyin_stream_url(douyin_url)
    print(f"主播: {streamer_name}")
    print(f"直播流地址: {stream_url}")
    
    if stream_url:
        # 开始录制，每1分钟一个文件，总共录制5分钟
        task_id = live_recorder.record_stream(stream_url, streamer_name, duration_minutes=5, segment_duration=60)
        print(f"录制任务ID: {task_id}")
        
        # 等待一段时间后检查状态
        time.sleep(10)
        status = live_recorder.get_recording_status(task_id)
        print(f"录制状态: {status}")
        
        # 提前停止录制的示例 (注释掉以允许完整录制测试)
        # time.sleep(120)  # 录制2分钟后停止
        # stopped = live_recorder.stop_recording(task_id)
        # print(f"停止录制: {'成功' if stopped else '失败'}")