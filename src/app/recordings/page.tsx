'use client';

import React from 'react';
import { Typography, Alert } from 'antd';
import AppLayout from '../../components/layout/AppLayout';

const { Title } = Typography;

export default function RecordingsPage() {
  return (
    <AppLayout>
      <div style={{ padding: '24px' }}>
        <Title level={2}>录音文件</Title>
        <Alert
          message="功能已移除"
          description="录音文件管理功能已被移除。请使用任务管理页面查看和管理音频文件。"
          type="info"
          showIcon
        />
      </div>
    </AppLayout>
  );
}
