'use client';

import React, { useState, useEffect } from 'react';
import { Typography, Card, Space, Badge, Button, Alert, App } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import AppLayout from '../../components/layout/AppLayout';

const { Title, Text } = Typography;

// API基础URL
const API_BASE_URL = 'http://localhost:8000';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 5000,
});

interface ServiceStatus {
  nlsApi: {
    status: 'online' | 'offline' | 'error';
    message: string;
  };
  dashscopeApi: {
    status: 'online' | 'offline' | 'error';
    message: string;
  };
}

// 状态页面组件
function StatusPageContent() {
  const { message: messageApi } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkServices = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/status');
      setStatus(response.data);
      messageApi.success('服务状态检查完成');
    } catch (err) {
      console.error('检查服务状态失败:', err);
      setError('无法连接到后端服务器，请确保服务已启动');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkServices();
  }, []);

  const getStatusBadge = (status: 'online' | 'offline' | 'error') => {
    switch (status) {
      case 'online':
        return <Badge status="success" text="在线" />;
      case 'offline':
        return <Badge status="default" text="离线" />;
      case 'error':
        return <Badge status="error" text="错误" />;
      default:
        return <Badge status="processing" text="检查中" />;
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Space align="center">
          <Title level={2} style={{ margin: 0 }}>服务状态</Title>
          <Button
            icon={<ReloadOutlined />}
            onClick={checkServices}
            loading={loading}
          >
            刷新
          </Button>
        </Space>

        {error && (
          <Alert
            message="连接错误"
            description={error}
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
          />
        )}

        {status && (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Card title="阿里云语音识别服务" bordered={false}>
              <Space direction="vertical">
                <div>
                  <Text strong>状态：</Text>
                  {getStatusBadge(status.nlsApi.status)}
                </div>
                <div>
                  <Text strong>详情：</Text>
                  <Text>{status.nlsApi.message}</Text>
                </div>
              </Space>
            </Card>

            <Card title="阿里云 DashScope 服务" bordered={false}>
              <Space direction="vertical">
                <div>
                  <Text strong>状态：</Text>
                  {getStatusBadge(status.dashscopeApi.status)}
                </div>
                <div>
                  <Text strong>详情：</Text>
                  <Text>{status.dashscopeApi.message}</Text>
                </div>
              </Space>
            </Card>
          </Space>
        )}
      </Space>
    </div>
  );
}

// 导出的主页面组件
export default function StatusPage() {
  return (
    <AppLayout>
      <App>
        <StatusPageContent />
      </App>
    </AppLayout>
  );
}
