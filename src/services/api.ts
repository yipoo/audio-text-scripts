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
export const generateScripts = async (jobId: string, numScripts: number = 5): Promise<any> => {
  try {
    const response = await api.post(`/api/jobs/${jobId}/generate-scripts?num_scripts=${numScripts}`);
    return response.data;
  } catch (error) {
    console.error('生成脚本失败:', error);
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
