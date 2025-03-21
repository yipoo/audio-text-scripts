'use client';

import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Table, 
  Button, 
  App,
  Space, 
  Tag,
  Tooltip,
  Empty,
  Spin,
  Alert,
  message,
  Modal,
  Tabs,
  InputNumber,
  Card,
  Dropdown,
  Menu
} from 'antd';
import { 
  ReloadOutlined, 
  CheckCircleOutlined, 
  SyncOutlined, 
  ClockCircleOutlined, 
  ExclamationCircleOutlined,
  RedoOutlined,
  FileTextOutlined,
  TagsOutlined,
  ScissorOutlined,
  MoreOutlined,
  DownOutlined,
  CopyOutlined
} from '@ant-design/icons';
import axios from 'axios';
import AppLayout from '../../components/layout/AppLayout';
import { fetchJobs, fetchJobTranscript, fetchJobTags, fetchJobScripts, generateScripts, generateTags, retryJob } from '../../services/api';

const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

// API基础URL
const API_BASE_URL = 'http://localhost:8000';

// 任务状态类型
type JobStatus = 'pending' | 'processing' | 'completed' | 'error';

// 任务类型
interface Job {
  job_id: string;
  status: JobStatus;
  filename: string;
  created_at: string;
  updated_at: string;
  message?: string;
}

// 格式化日期函数
const formatDate = (dateStr: string): string => {
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (error) {
    return '无效日期';
  }
};

export default function JobsPage() {
  const { message: messageApi } = App.useApp();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [transcriptModalVisible, setTranscriptModalVisible] = useState<boolean>(false);
  const [currentTranscript, setCurrentTranscript] = useState<string>('');
  const [loadingTranscript, setLoadingTranscript] = useState<boolean>(false);
  const [currentJobId, setCurrentJobId] = useState<string>('');
  const [tagsModalVisible, setTagsModalVisible] = useState<boolean>(false);
  const [currentTags, setCurrentTags] = useState<string[]>([]);
  const [loadingTags, setLoadingTags] = useState<boolean>(false);
  const [scriptsModalVisible, setScriptsModalVisible] = useState<boolean>(false);
  const [currentScripts, setCurrentScripts] = useState<any>({ original_text: '', scripts: [] });
  const [loadingScripts, setLoadingScripts] = useState<boolean>(false);
  const [numScripts, setNumScripts] = useState<number>(5);
  const [generatingScripts, setGeneratingScripts] = useState<boolean>(false);
  
  const tagColors = ['blue', 'green', 'purple', 'magenta', 'cyan', 'orange'];

  // 获取任务列表
  const fetchJobsList = async () => {
    try {
      setLoading(true);
      setApiError(null);
      const response = await fetchJobs();
      
      // 按创建时间降序排序
      const sortedJobs = (response || []).sort((a: Job, b: Job) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      
      setJobs(sortedJobs);
    } catch (error) {
      console.error('获取任务列表失败:', error);
      setApiError('无法连接到后端服务器，请确保服务已启动。');
    } finally {
      setLoading(false);
    }
  };

  // 查看转写结果
  const handleViewTranscript = async (jobId: string) => {
    try {
      setCurrentJobId(jobId);
      setLoadingTranscript(true);
      setTranscriptModalVisible(true);
      
      const transcript = await fetchJobTranscript(jobId);
      setCurrentTranscript(transcript);
    } catch (error: any) {
      console.error('获取转写结果失败:', error);
      if (error.response && error.response.status === 400) {
        setCurrentTranscript(`错误: ${error.response.data.detail || '任务尚未完成'}`);
      } else {
        setCurrentTranscript('获取转写结果失败，请稍后再试');
      }
    } finally {
      setLoadingTranscript(false);
    }
  };

  // 查看标签
  const handleViewTags = async (jobId: string) => {
    try {
      setCurrentJobId(jobId);
      setLoadingTags(true);
      setTagsModalVisible(true);
      
      const tags = await fetchJobTags(jobId);
      setCurrentTags(tags);
    } catch (error: any) {
      console.error('获取标签失败:', error);
      if (error.response && error.response.status === 400) {
        setCurrentTags([`错误: ${error.response.data.detail || '任务尚未完成'}`]);
      } else if (error.response && error.response.status === 404) {
        setCurrentTags(['标签文件不存在，请先生成标签']);
      } else {
        setCurrentTags(['获取标签失败，请稍后再试']);
      }
    } finally {
      setLoadingTags(false);
    }
  };

  // 查看脚本
  const handleViewScripts = async (jobId: string) => {
    try {
      setCurrentJobId(jobId);
      setLoadingScripts(true);
      setScriptsModalVisible(true);
      
      const scripts = await fetchJobScripts(jobId);
      setCurrentScripts(scripts);
    } catch (error: any) {
      console.error('获取脚本失败:', error);
      if (error.response && error.response.status === 400) {
        setCurrentScripts({ 
          original_text: '', 
          scripts: [`错误: ${error.response.data.detail || '任务尚未完成'}`] 
        });
      } else if (error.response && error.response.status === 404) {
        setCurrentScripts({ 
          original_text: '', 
          scripts: ['脚本文件不存在，请先生成脚本'] 
        });
      } else {
        setCurrentScripts({ 
          original_text: '', 
          scripts: ['获取脚本失败，请稍后再试'] 
        });
      }
    } finally {
      setLoadingScripts(false);
    }
  };

  // 生成脚本
  const handleGenerateScripts = async () => {
    try {
      setGeneratingScripts(true);
      
      await generateScripts(currentJobId, numScripts);
      messageApi.success(`已开始生成 ${numScripts} 份脚本，请稍后刷新查看`);
      
      // 关闭脚本模态框
      setScriptsModalVisible(false);
      
      // 刷新任务列表
      fetchJobsList();
    } catch (error: any) {
      console.error('生成脚本失败:', error);
      messageApi.error('生成脚本失败，请稍后再试');
    } finally {
      setGeneratingScripts(false);
    }
  };

  // 生成标签
  const handleGenerateTags = async () => {
    try {
      setLoadingTags(true);
      
      await generateTags(currentJobId);
      messageApi.success('已开始生成标签，请稍后刷新查看');
      
      // 关闭标签模态框
      setTagsModalVisible(false);
      
      // 刷新任务列表
      fetchJobsList();
    } catch (error: any) {
      console.error('生成标签失败:', error);
      messageApi.error('生成标签失败，请稍后再试');
    } finally {
      setLoadingTags(false);
    }
  };

  // 重试失败的任务
  const handleRetry = async (jobId: string) => {
    try {
      setApiError(null);
      await retryJob(jobId);
      messageApi.success('任务已重新开始处理');
      fetchJobsList();
    } catch (error) {
      console.error('重试任务失败:', error);
      messageApi.error('重试任务失败，请稍后再试');
    }
  };

  // 组件挂载时获取任务列表
  useEffect(() => {
    fetchJobsList();
    
    // 每10秒自动刷新一次
    const intervalId = setInterval(fetchJobsList, 10000);
    
    // 组件卸载时清除定时器
    return () => clearInterval(intervalId);
  }, []);

  // 获取状态标签
  const getStatusTag = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return (
          <Tag icon={<CheckCircleOutlined />} color="success">
            已完成
          </Tag>
        );
      case 'processing':
        return (
          <Tag icon={<SyncOutlined spin />} color="processing">
            处理中
          </Tag>
        );
      case 'pending':
        return (
          <Tag icon={<ClockCircleOutlined />} color="default">
            等待中
          </Tag>
        );
      case 'error':
        return (
          <Tag icon={<ExclamationCircleOutlined />} color="error">
            失败
          </Tag>
        );
      default:
        return (
          <Tag color="default">
            未知状态
          </Tag>
        );
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      width: '30%',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: JobStatus, record: Job) => (
        <Tooltip title={record.message}>
          {getStatusTag(status)}
        </Tooltip>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => formatDate(date),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date: string) => formatDate(date),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          {record.status === 'error' && (
            <Button
              type="link"
              icon={<RedoOutlined />}
              onClick={() => handleRetry(record.job_id)}
            >
              重试
            </Button>
          )}
          {record.status === 'completed' && (
            <Dropdown
              overlay={
                <Menu>
                  <Menu.Item 
                    key="transcript" 
                    icon={<FileTextOutlined />}
                    onClick={() => handleViewTranscript(record.job_id)}
                  >
                    查看转写结果
                  </Menu.Item>
                  <Menu.Item 
                    key="tags" 
                    icon={<TagsOutlined />}
                    onClick={() => handleViewTags(record.job_id)}
                  >
                    查看标签
                  </Menu.Item>
                  <Menu.Item 
                    key="scripts" 
                    icon={<ScissorOutlined />}
                    onClick={() => handleViewScripts(record.job_id)}
                  >
                    查看脚本
                  </Menu.Item>
                </Menu>
              }
              trigger={['click']}
            >
              <Button type="primary">
                查看内容 <DownOutlined />
              </Button>
            </Dropdown>
          )}
        </Space>
      ),
    },
  ];

  return (
    <AppLayout>
      <App>
        <div style={{ padding: '24px' }}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Space>
              <Title level={3}>任务管理</Title>
              <Button 
                type="primary" 
                icon={<ReloadOutlined />} 
                onClick={fetchJobsList}
                loading={loading}
              >
                刷新
              </Button>
            </Space>

            {apiError && (
              <Alert
                message="连接错误"
                description={apiError}
                type="error"
                showIcon
                closable
                onClose={() => setApiError(null)}
              />
            )}

            {loading ? (
              <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin size="large" />
              </div>
            ) : jobs.length === 0 ? (
              <Empty description="暂无任务" />
            ) : (
              <Table
                columns={columns}
                dataSource={jobs}
                rowKey="job_id"
                pagination={{
                  hideOnSinglePage: true,
                  pageSize: 10,
                }}
              />
            )}
          </Space>
        </div>
        <Modal
          title="转写结果"
          open={transcriptModalVisible}
          onCancel={() => setTranscriptModalVisible(false)}
          footer={null}
        >
          {loadingTranscript ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Spin size="large" />
            </div>
          ) : (
            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              {currentTranscript}
            </pre>
          )}
        </Modal>
        <Modal
          title="标签"
          open={tagsModalVisible}
          onCancel={() => setTagsModalVisible(false)}
          footer={null}
          width={800}
        >
          {loadingTags ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Spin size="large" />
              <div style={{ marginTop: '10px' }}>加载中...</div>
            </div>
          ) : (
            <div>
              <Tabs defaultActiveKey="view">
                <TabPane tab="查看标签" key="view">
                  <div style={{ marginTop: '16px' }}>
                    {currentTags && currentTags.length > 0 ? (
                      <div>
                        {currentTags.map((tag: string, index: number) => (
                          <Tag
                            key={index}
                            color={tagColors[index % tagColors.length]}
                            style={{ margin: '5px', fontSize: '14px', padding: '5px 10px' }}
                          >
                            {tag}
                          </Tag>
                        ))}
                      </div>
                    ) : (
                      <Empty description="暂无标签" />
                    )}
                  </div>
                </TabPane>
                <TabPane tab="生成标签" key="generate">
                  <div style={{ marginTop: '16px', textAlign: 'center' }}>
                    <Alert
                      message="生成标签"
                      description="点击下方按钮，系统将根据转写文本自动提取关键词作为标签。"
                      type="info"
                      showIcon
                      style={{ marginBottom: '20px' }}
                    />
                    <Button
                      type="primary"
                      icon={<TagsOutlined />}
                      onClick={handleGenerateTags}
                      loading={loadingTags}
                      size="large"
                    >
                      开始生成标签
                    </Button>
                  </div>
                </TabPane>
              </Tabs>
            </div>
          )}
        </Modal>
        <Modal
          title="脚本"
          open={scriptsModalVisible}
          onCancel={() => setScriptsModalVisible(false)}
          footer={null}
          width={800}
        >
          {loadingScripts ? (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Spin size="large" />
              <div style={{ marginTop: '10px' }}>加载中...</div>
            </div>
          ) : (
            <div>
              <Tabs defaultActiveKey="scripts">
                <TabPane tab="原文" key="transcript">
                  <div style={{ marginTop: '16px' }}>
                    {currentTranscript ? (
                      <Card>
                        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                          {currentTranscript}
                        </pre>
                      </Card>
                    ) : (
                      <Empty description="暂无转写结果" />
                    )}
                  </div>
                </TabPane>
                <TabPane tab="脚本" key="scripts">
                  <div style={{ marginTop: '16px' }}>
                    {currentScripts.scripts && currentScripts.scripts.length > 0 ? (
                      <div>
                        {currentScripts.scripts.map((script: string, index: number) => (
                          <Card
                            key={index}
                            title={`脚本 ${index + 1}`}
                            style={{ marginBottom: '16px' }}
                            extra={
                              <Tooltip title="复制">
                                <Button
                                  type="text"
                                  icon={<CopyOutlined />}
                                  onClick={() => {
                                    navigator.clipboard.writeText(script);
                                    messageApi.success('已复制到剪贴板');
                                  }}
                                />
                              </Tooltip>
                            }
                          >
                            <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                              {script}
                            </pre>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <Empty description="暂无脚本" />
                    )}
                  </div>
                </TabPane>
                <TabPane tab="生成脚本" key="generate">
                  <div style={{ marginTop: '16px', textAlign: 'center' }}>
                    <Alert
                      message="生成脚本"
                      description="设置要生成的脚本数量，然后点击生成按钮。系统将根据转写文本和标签自动生成多个脚本变体。"
                      type="info"
                      showIcon
                      style={{ marginBottom: '20px' }}
                    />
                    <div style={{ marginBottom: '20px' }}>
                      <span style={{ marginRight: '10px' }}>脚本数量：</span>
                      <InputNumber
                        min={1}
                        max={10}
                        defaultValue={numScripts}
                        onChange={(value) => setNumScripts(value || 5)}
                      />
                    </div>
                    <Button
                      type="primary"
                      icon={<ScissorOutlined />}
                      onClick={handleGenerateScripts}
                      loading={generatingScripts}
                      size="large"
                    >
                      开始生成脚本
                    </Button>
                  </div>
                </TabPane>
              </Tabs>
            </div>
          )}
        </Modal>
      </App>
    </AppLayout>
  );
}
