import axios from 'axios';
import { Job, RecordingFile } from '@/types';

// API基础URL
const API_BASE_URL = 'http://localhost:8000';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,
});

// 直播录制相关接口类型定义
export interface LiveStreamRequest {
  url: string;
  duration_minutes?: number;
  segment_duration?: number;
}

export interface TaskResponse {
  task_id: string;
  message: string;
}

export interface RecordingStatus {
  status: string;
  start_time?: string;
  duration?: number;
  file_path?: string;
  error?: string;
}

// 开始录制直播
export const startRecording = async (request: LiveStreamRequest): Promise<TaskResponse> => {
  try {
    console.log('开始录制直播请求:', request);
    const response = await api.post('/api/livestream/start', request);
    console.log('开始录制直播成功:', response.data);
    return response.data;
  } catch (error) {
    console.error('开始录制直播失败:', error);
    throw error;
  }
};

// 获取录制任务状态
export const getRecordingStatus = async (taskId: string): Promise<RecordingStatus> => {
  try {
    const response = await api.get(`/api/livestream/status/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('获取录制状态失败:', error);
    throw error;
  }
};

// 获取所有录制任务状态
export const getAllRecordingTasks = async (): Promise<Record<string, RecordingStatus>> => {
  try {
    const response = await api.get('/api/livestream/status');
    return response.data;
  } catch (error) {
    console.error('获取所有录制任务状态失败:', error);
    throw error;
  }
};

// 停止录制任务
export const stopRecording = async (taskId: string): Promise<{ success: boolean; message: string; status: RecordingStatus }> => {
  try {
    const response = await api.post(`/api/livestream/stop/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('停止录制失败:', error);
    throw error;
  }
};

// 获取任务列表
export const fetchJobs = async (): Promise<Job[]> => {
  try {
    const response = await api.get('/api/jobs');
    return response.data || [];
  } catch (error) {
    console.error('获取任务列表失败:', error);
    throw error;
  }
};

// 获取任务详情
export const fetchJobDetails = async (jobId: string): Promise<any> => {
  try {
    const response = await api.get(`/api/jobs/${jobId}`);
    return response.data;
  } catch (error) {
    console.error('获取任务详情失败:', error);
    throw error;
  }
};

// 获取任务转写结果
export const fetchJobTranscript = async (jobId: string): Promise<string> => {
  try {
    const response = await api.get(`/api/jobs/${jobId}/transcript`);
    return response.data.transcript || '';
  } catch (error) {
    console.error('获取转写结果失败:', error);
    throw error;
  }
};

// 获取任务标签
export const fetchJobTags = async (jobId: string): Promise<string[]> => {
  try {
    const response = await api.get(`/api/jobs/${jobId}/tags`);
    return response.data.tags || [];
  } catch (error) {
    console.error('获取标签失败:', error);
    throw error;
  }
};

// 获取任务脚本
export const fetchJobScripts = async (jobId: string): Promise<any> => {
  try {
    const response = await api.get(`/api/jobs/${jobId}/scripts`);
    return response.data.scripts || { original_text: '', scripts: [] };
  } catch (error) {
    console.error('获取脚本失败:', error);
    throw error;
  }
};

// 重试任务
export const retryJob = async (jobId: string): Promise<any> => {
  try {
    const response = await api.post(`/api/jobs/${jobId}/retry`);
    return response.data;
  } catch (error) {
    console.error('重试任务失败:', error);
    throw error;
  }
};

// 生成标签
export const generateTags = async (jobId: string): Promise<any> => {
  try {
    const response = await api.post(`/api/jobs/${jobId}/generate-tags`);
    return response.data;
  } catch (error) {
    console.error('生成标签失败:', error);
    throw error;
  }
};

// 生成脚本
export const generateScripts = async (
  jobId: string, 
  numScripts: number = 5, 
  customPrompt?: string,
  overwrite: boolean = false
): Promise<any> => {
  try {
    const params = new URLSearchParams();
    params.append('num_scripts', numScripts.toString());
    
    if (customPrompt) {
      params.append('custom_prompt', customPrompt);
    }
    
    params.append('overwrite', overwrite.toString());
    
    const response = await api.post(`/api/jobs/${jobId}/generate-scripts?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('生成脚本失败:', error);
    throw error;
  }
};

// 获取所有脚本
export const fetchAllScripts = async (): Promise<any> => {
  try {
    // 获取所有任务
    const jobs = await fetchJobs();
    
    // 筛选出已完成的任务
    const completedJobs = jobs.filter((job: any) => job.status === 'completed');
    
    // 获取每个任务的脚本和标签
    const scriptGroupsData = [];
    
    for (const job of completedJobs) {
      try {
        const scripts = await fetchJobScripts(job.job_id);
        const tags = await fetchJobTags(job.job_id);
        
        if (scripts && scripts.scripts && scripts.scripts.length > 0) {
          // 为每个脚本添加ID
          const scriptsWithIds = scripts.scripts.map((content: string, index: number) => ({
            id: `${job.job_id}-${index}`,
            content,
            source_job_id: job.job_id,
            created_at: job.updated_at || job.created_at
          }));
          
          // 添加到脚本组
          scriptGroupsData.push({
            original_text: scripts.original_text || '无原文',
            job_id: job.job_id,
            scripts: scriptsWithIds,
            tags: tags || [],
            created_at: job.updated_at || job.created_at
          });
        }
      } catch (error) {
        console.error(`获取任务 ${job.job_id} 的脚本失败:`, error);
      }
    }
    
    // 按创建时间排序，最新的在前面
    scriptGroupsData.sort((a, b) => {
      const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
      const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
      return dateB - dateA;
    });
    
    return scriptGroupsData;
  } catch (error) {
    console.error('获取所有脚本失败:', error);
    throw error;
  }
};

// 上传音频文件
export const uploadAudio = async (
  file: File,
  onProgress?: (percent: number) => void
): Promise<any> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percent);
        }
      },
    });
    return response.data;
  } catch (error) {
    console.error('上传音频文件失败:', error);
    throw error;
  }
};
