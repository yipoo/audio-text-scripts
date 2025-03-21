'use client';

import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Upload, 
  Button, 
  Card, 
  Row, 
  Col, 
  Statistic,
  Space,
  Alert,
  Spin,
  App
} from 'antd';
import { 
  InboxOutlined, 
  SoundOutlined, 
  FileTextOutlined, 
  RobotOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';
import axios from 'axios';
import AppLayout from '../components/layout/AppLayout';
import { fetchJobs } from '../services/api';

const { Title, Paragraph } = Typography;
const { Dragger } = Upload;

// API基础URL
const API_BASE_URL = 'http://localhost:8000';

export default function HomePage() {
  const { message } = App.useApp();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [stats, setStats] = useState({
    totalJobs: 0,
    completedJobs: 0,
  });
  const [apiError, setApiError] = useState<string | null>(null);

  // 获取统计数据
  const fetchStats = async () => {
    try {
      setLoading(true);
      setApiError(null);
      // 获取任务列表
      const jobs = await fetchJobs();
      const completedJobs = jobs.filter(job => job.status === 'completed');
      
      setStats({
        totalJobs: jobs.length,
        completedJobs: completedJobs.length,
      });
    } catch (error) {
      console.error('获取统计数据失败:', error);
      setApiError('无法连接到后端服务器，请确保服务已启动。');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载时获取统计数据
  useEffect(() => {
    fetchStats();
  }, []);

  // 文件上传处理
  const handleUpload = async (options: any) => {
    const { file, onSuccess, onError, onProgress } = options;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      setUploading(true);
      setApiError(null);
      
      const response = await axios.post(`${API_BASE_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          onProgress({ percent });
        },
      });
      
      onSuccess(response.data);
      message.success(`${file.name} 上传成功，正在处理中...`);
      
      // 上传成功后清空文件列表并刷新统计数据
      setFileList([]);
      fetchStats();
    } catch (error) {
      console.error('上传失败:', error);
      message.error(`${file.name} 上传失败`);
      setApiError('上传文件失败，请确保服务已启动。');
      onError();
    } finally {
      setUploading(false);
    }
  };
  
  const handleUploadChange = (info: any) => {
    let newFileList = [...info.fileList];
    
    // 只保留最后一个文件
    newFileList = newFileList.slice(-1);
    
    setFileList(newFileList);
  };
  
  const handleRemove = () => {
    setFileList([]);
    return true;
  };

  return (
    <AppLayout>
      <div>
        <Title level={2}>短视频营销内容生成</Title>
        <Paragraph>
          上传抖音直播录音，自动转写文字并生成多份营销话术
        </Paragraph>
        
        {apiError && (
          <Alert
            message="连接错误"
            description={apiError}
            type="error"
            showIcon
            closable
            style={{ marginBottom: 24 }}
            onClose={() => setApiError(null)}
          />
        )}
        
        <Space align="center" style={{ marginBottom: 24 }}>
          <Title level={3}>服务状态</Title>
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={fetchStats}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
        
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="总任务数"
                value={stats.totalJobs}
                prefix={<SoundOutlined />}
                loading={loading}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="已完成任务"
                value={stats.completedJobs}
                prefix={<FileTextOutlined />}
                loading={loading}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="完成率"
                value={stats.totalJobs > 0 ? (stats.completedJobs / stats.totalJobs * 100).toFixed(1) : 0}
                suffix="%"
                prefix={<RobotOutlined />}
                loading={loading}
              />
            </Card>
          </Col>
        </Row>
        
        <Card title="上传音频文件" style={{ marginBottom: 24 }}>
          <Spin spinning={loading}>
            <Dragger
              name="file"
              multiple={false}
              fileList={fileList}
              customRequest={handleUpload}
              onChange={handleUploadChange}
              onRemove={handleRemove}
              accept=".wav,.mp3,.m4a"
              showUploadList={true}
              progress={{
                strokeColor: {
                  '0%': '#108ee9',
                  '100%': '#87d068',
                },
                strokeWidth: 3,
                format: (percent) => `${percent}%`,
              }}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持单个音频文件上传 (.wav, .mp3, .m4a)</p>
            </Dragger>
          </Spin>
        </Card>
        
        <Space>
          <Button 
            type="primary" 
            href="/jobs"
          >
            查看处理任务
          </Button>
        </Space>
      </div>
    </AppLayout>
  );
}
