'use client';

import React, { useState, useEffect } from 'react';
import {
    Card,
    Form,
    Input,
    Button,
    InputNumber,
    Table,
    Tag,
    Space,
    message,
    Typography,
    Modal,
    Spin,
    Divider,
    App,
} from 'antd';
import { PlayCircleOutlined, StopOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import AppLayout from '@/src/components/layout/AppLayout';
import { startRecording, getRecordingStatus, getAllRecordingTasks, stopRecording } from '../../services/api';
import { LiveStreamRequest, RecordingStatus } from '../../types';

const { Title, Text } = Typography;

interface LiveStreamFormData {
    url: string;
    duration_minutes?: number;
    segment_duration: number;
}

interface RecordingTask {
    task_id: string;
    streamer_name: string;
    start_time: string;
    status: 'recording' | 'stopped' | 'completed' | 'error';
    duration_minutes?: number;
    segment_duration: number;
    output_dir: string;
    stream_url: string;
    end_time?: string;
}

const LiveStreamPage: React.FC = () => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [tasks, setTasks] = useState<RecordingTask[]>([]);

    // 加载任务列表
    const fetchTasks = async () => {
        try {
            setRefreshing(true);
            const response = await getAllRecordingTasks();

            // 将对象转换为数组
            const tasksData = Object.entries(response).map(([task_id, taskInfo]) => ({
                task_id,
                ...(taskInfo as any)
            }));

            setTasks(tasksData);
        } catch (error) {
            console.error('获取录制任务失败:', error);
            message.error('获取录制任务列表失败');
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchTasks();

        // 设置定时刷新 (每30秒)
        const interval = setInterval(fetchTasks, 30000);
        return () => clearInterval(interval);
    }, []);

    // 提交表单开始录制
    const handleSubmit = async (values: LiveStreamFormData) => {
        try {
            setLoading(true);

            // 显示正在获取直播流的提示
            message.loading({ content: '正在获取直播流地址...', key: 'streamLoading', duration: 0 });

            const response = await startRecording(values);
            const taskId = response.task_id;

            // 显示成功消息，包含主播名称(如果有的话)
            message.success({ 
                content: response.message || '录制任务已启动', 
                key: 'streamLoading' 
            });

            console.log('录制任务已启动:', response);

            // 立即获取一次任务列表，然后设置定时器再次获取
            fetchTasks();
            setTimeout(() => {
                fetchTasks();
            }, 5000);

            form.resetFields();
        } catch (error: any) {
            console.error('提交录制任务失败:', error);
            const errorMessage = error.response?.data?.detail || '录制任务提交失败';
            message.error({ content: errorMessage, key: 'streamLoading' });
        } finally {
            setLoading(false);
        }
    };

    // 停止录制任务
    const stopTask = async (taskId: string) => {
        try {
            const result = await stopRecording(taskId);
            if (result.success) {
                message.success(result.message || '录制任务已停止');
            } else {
                message.error(result.message || '停止录制任务失败');
            }
            fetchTasks();
        } catch (error) {
            console.error('停止录制任务失败:', error);
            message.error('停止录制任务失败');
        }
    };

    // 确认停止录制
    const confirmStopTask = (taskId: string, streamerName: string) => {
        Modal.confirm({
            title: '确认停止录制',
            content: `确定要停止录制 "${streamerName}" 的直播吗？`,
            onOk: () => stopTask(taskId),
        });
    };

    // 格式化时间
    const formatDateTime = (dateString: string) => {
        return new Date(dateString).toLocaleString('zh-CN');
    };

    // 表格列配置
    const columns = [
        {
            title: '主播',
            dataIndex: 'streamer_name',
            key: 'streamer_name',
        },
        {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                let color = 'default';
                let text = status;

                switch (status) {
                    case 'recording':
                        color = 'green';
                        text = '录制中';
                        break;
                    case 'stopped':
                        color = 'orange';
                        text = '已停止';
                        break;
                    case 'completed':
                        color = 'blue';
                        text = '已完成';
                        break;
                    case 'error':
                        color = 'red';
                        text = '错误';
                        break;
                }

                return <Tag color={color}>{text}</Tag>;
            },
        },
        {
            title: '开始时间',
            dataIndex: 'start_time',
            key: 'start_time',
            render: (time: string) => formatDateTime(time),
        },
        {
            title: '结束时间',
            dataIndex: 'end_time',
            key: 'end_time',
            render: (time: string) => time ? formatDateTime(time) : '-',
        },
        {
            title: '录制时长',
            key: 'duration',
            render: (_: unknown, record: RecordingTask) => {
                if (record.duration_minutes) {
                    return `${record.duration_minutes} 分钟`;
                }

                if (record.status === 'recording') {
                    const startTime = new Date(record.start_time).getTime();
                    const now = new Date().getTime();
                    const durationMinutes = Math.floor((now - startTime) / (1000 * 60));
                    return `${durationMinutes} 分钟 (进行中)`;
                }

                if (record.end_time) {
                    const startTime = new Date(record.start_time).getTime();
                    const endTime = new Date(record.end_time).getTime();
                    const durationMinutes = Math.floor((endTime - startTime) / (1000 * 60));
                    return `${durationMinutes} 分钟`;
                }

                return '-';
            },
        },
        {
            title: '操作',
            key: 'action',
            render: (_: unknown, record: RecordingTask) => (
                <Space size="small">
                    {record.status === 'recording' && (
                        <Button
                            type="primary"
                            danger
                            icon={<StopOutlined />}
                            onClick={() => confirmStopTask(record.task_id, record.streamer_name)}
                        >
                            停止
                        </Button>
                    )}
                </Space>
            ),
        },
    ];

    return (
        <AppLayout>
            <App>
                <div>
                    <Title level={2}>直播录制</Title>

                    <Card title="新建录制任务" style={{ marginBottom: 24 }}>
                        <Form
                            form={form}
                            layout="vertical"
                            onFinish={handleSubmit}
                            initialValues={{ segment_duration: 60 }}
                        >
                            <Form.Item
                                name="url"
                                label="直播URL"
                                rules={[{ required: true, message: '请输入直播URL' }]}
                                help="输入抖音直播间URL，例如：https://live.douyin.com/xxxxx"
                            >
                                <Input placeholder="请输入抖音直播URL" />
                            </Form.Item>

                            <Form.Item
                                name="duration_minutes"
                                label="录制时长 (分钟)"
                                help="留空表示持续录制直到手动停止"
                            >
                                <InputNumber min={1} style={{ width: '100%' }} placeholder="留空表示持续录制直到手动停止" />
                            </Form.Item>

                            <Form.Item
                                name="segment_duration"
                                label="分段时长 (秒)"
                                help="每个录音文件的长度"
                                rules={[{ required: true, message: '请输入分段时长' }]}
                            >
                                <InputNumber min={10} max={3600} style={{ width: '100%' }} />
                            </Form.Item>

                            <Form.Item>
                                <Button
                                    type="primary"
                                    htmlType="submit"
                                    loading={loading}
                                    icon={<PlayCircleOutlined />}
                                >
                                    开始录制
                                </Button>
                            </Form.Item>
                        </Form>
                    </Card>

                    <Card
                        title="录制任务列表"
                        extra={
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={fetchTasks}
                                loading={refreshing}
                            >
                                刷新
                            </Button>
                        }
                    >
                        <Table
                            columns={columns}
                            dataSource={tasks}
                            rowKey="task_id"
                            loading={refreshing}
                            pagination={false}
                            locale={{ emptyText: '暂无录制任务' }}
                        />
                    </Card>
                </div>
            </App>
        </AppLayout>
    );
};

export default LiveStreamPage; 