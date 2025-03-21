'use client';

import React, { useState, useEffect } from 'react';
import { Typography, Card, Space, Badge, Button, Alert, App, Spin, Collapse, Tag, Table, Tooltip } from 'antd';
import { ReloadOutlined, CheckCircleOutlined, InfoCircleOutlined, ClockCircleOutlined, SyncOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import AppLayout from '../../components/layout/AppLayout';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

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
  lastCheck?: string;
  logs?: string[];
}

interface BackgroundTask {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  start_time: string;
  end_time: string | null;
  args: string;
  kwargs: string;
  result: string | null;
  error: string | null;
}

interface SystemStatus {
  active_tasks: number;
  total_tasks: number;
  thread_pool: {
    max_workers: number;
    active_threads: number;
    tasks_completed: number;
  };
  recent_tasks: BackgroundTask[];
}

// 状态页面组件
function StatusPageContent() {
  const { message: messageApi } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<ServiceStatus | null>({
    nlsApi: { status: 'offline', message: '正在检查...' },
    dashscopeApi: { status: 'offline', message: '正在检查...' }
  });
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tasksLoading, setTasksLoading] = useState(false);

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

  const fetchSystemStatus = async () => {
    try {
      setTasksLoading(true);
      const response = await api.get('/api/system/status');
      setSystemStatus(response.data);
    } catch (err) {
      console.error('获取系统状态失败:', err);
    } finally {
      setTasksLoading(false);
    }
  };

  useEffect(() => {
    // 立即显示页面内容，然后异步加载状态
    checkServices();
    fetchSystemStatus();

    // 每10秒刷新一次系统状态
    const intervalId = setInterval(() => {
      fetchSystemStatus();
    }, 10000);

    return () => clearInterval(intervalId);
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

  const getTaskStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge status="warning" text={<><ClockCircleOutlined /> 等待中</>} />;
      case 'running':
        return <Badge status="processing" text={<><SyncOutlined spin /> 运行中</>} />;
      case 'completed':
        return <Badge status="success" text={<><CheckCircleOutlined /> 已完成</>} />;
      case 'error':
        return <Badge status="error" text={<><CloseCircleOutlined /> 错误</>} />;
      default:
        return <Badge status="default" text="未知" />;
    }
  };

  const formatLogEntry = (log: string) => {
    if (log.includes('INFO')) {
      return <Text style={{ color: '#1890ff' }}>{log}</Text>;
    } else if (log.includes('ERROR')) {
      return <Text type="danger">{log}</Text>;
    } else if (log.includes('WARNING')) {
      return <Text type="warning">{log}</Text>;
    }
    return <Text>{log}</Text>;
  };

  // 判断服务是否全部在线
  const allServicesOnline = status?.nlsApi.status === 'online' && status?.dashscopeApi.status === 'online';

  // 任务列表表格列定义
  const taskColumns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getTaskStatusBadge(status)
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      render: (time: string) => new Date(time).toLocaleString()
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      render: (time: string | null) => time ? new Date(time).toLocaleString() : '-'
    },
    {
      title: '参数',
      dataIndex: 'args',
      key: 'args',
      render: (args: string, record: BackgroundTask) => (
        <Tooltip title={`参数: ${args}, 关键字参数: ${record.kwargs}`}>
          <Tag color="blue">查看参数</Tag>
        </Tooltip>
      )
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      render: (result: string | null, record: BackgroundTask) => {
        if (record.status === 'error' && record.error) {
          return <Tooltip title={record.error}><Tag color="red">错误</Tag></Tooltip>;
        }
        if (result) {
          return <Tooltip title={result}><Tag color="green">成功</Tag></Tooltip>;
        }
        return '-';
      }
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Space align="center">
          <Title level={2} style={{ margin: 0 }}>服务状态</Title>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              checkServices();
              fetchSystemStatus();
            }}
            loading={loading || tasksLoading}
          >
            刷新
          </Button>
        </Space>

        {allServicesOnline && !loading && (
          <Alert
            message="所有服务正常运行"
            description="阿里云语音识别服务和DashScope服务均已连接成功，可以正常使用。"
            type="success"
            showIcon
            icon={<CheckCircleOutlined />}
          />
        )}

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

        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Card title="阿里云语音识别服务" variant="borderless">
            <Space direction="vertical">
              <div>
                <Text strong>状态：</Text>
                {loading && status?.nlsApi.status !== 'online' ? 
                  <Badge status="processing" text={<Spin size="small" />} /> : 
                  getStatusBadge(status?.nlsApi.status || 'offline')}
              </div>
              <div>
                <Text strong>详情：</Text>
                <Text>{status?.nlsApi.message || '正在检查...'}</Text>
              </div>
            </Space>
          </Card>

          <Card title="阿里云 DashScope 服务" variant="borderless">
            <Space direction="vertical">
              <div>
                <Text strong>状态：</Text>
                {loading && status?.dashscopeApi.status !== 'online' ? 
                  <Badge status="processing" text={<Spin size="small" />} /> : 
                  getStatusBadge(status?.dashscopeApi.status || 'offline')}
              </div>
              <div>
                <Text strong>详情：</Text>
                <Text>{status?.dashscopeApi.message || '正在检查...'}</Text>
              </div>
            </Space>
          </Card>

          {/* 系统状态卡片 */}
          <Card 
            title="系统资源状态" 
            variant="borderless"
            extra={
              <Button 
                type="text" 
                icon={<ReloadOutlined />} 
                onClick={fetchSystemStatus} 
                loading={tasksLoading}
              />
            }
          >
            {systemStatus ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div>
                    <Text strong>活跃任务：</Text>
                    <Tag color="blue">{systemStatus.active_tasks}</Tag>
                  </div>
                  <div>
                    <Text strong>总任务数：</Text>
                    <Tag color="default">{systemStatus.total_tasks}</Tag>
                  </div>
                  <div>
                    <Text strong>最大工作线程：</Text>
                    <Tag color="default">{systemStatus.thread_pool.max_workers}</Tag>
                  </div>
                  <div>
                    <Text strong>活跃线程：</Text>
                    <Tag color="green">{systemStatus.thread_pool.active_threads}</Tag>
                  </div>
                </div>
              </Space>
            ) : (
              <Spin />
            )}
          </Card>

          {/* 后台任务表格 */}
          <Card 
            title="后台任务状态" 
            variant="borderless"
            extra={
              <Button 
                type="text" 
                icon={<ReloadOutlined />} 
                onClick={fetchSystemStatus} 
                loading={tasksLoading}
              />
            }
          >
            {systemStatus ? (
              <Table 
                dataSource={systemStatus.recent_tasks} 
                columns={taskColumns} 
                rowKey="id"
                size="small"
                pagination={false}
                loading={tasksLoading}
              />
            ) : (
              <Spin />
            )}
          </Card>

          {status?.lastCheck && (
            <div style={{ textAlign: 'right' }}>
              <Text type="secondary">
                最后检查时间: {new Date(status.lastCheck).toLocaleString()}
              </Text>
            </div>
          )}

          {status?.logs && status.logs.length > 0 && (
            <Collapse ghost>
              <Panel header={<Text><InfoCircleOutlined /> 查看详细日志</Text>} key="1">
                <Card size="small" style={{ maxHeight: '300px', overflow: 'auto' }} variant="borderless">
                  {status.logs.map((log, index) => (
                    <div key={index} style={{ marginBottom: '4px' }}>
                      {formatLogEntry(log)}
                    </div>
                  ))}
                </Card>
              </Panel>
            </Collapse>
          )}
        </Space>
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
