'use client';

import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Checkbox, Card, Typography, message, Divider } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

const { Title, Text } = Typography;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login, user } = useAuth();
  
  // 如果用户已登录，重定向到首页
  useEffect(() => {
    if (user) {
      router.push('/');
    }
  }, [user, router]);

  const onFinish = async (values: any) => {
    try {
      setLoading(true);
      await login(values.username, values.password);
      message.success('登录成功！');
      router.push('/');
    } catch (error) {
      console.error('登录失败:', error);
      message.error('登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      background: '#f0f2f5'
    }}>
      <Card 
        style={{ 
          width: 400, 
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          borderRadius: '8px'
        }}
        bordered={false}
      >
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2} style={{ marginBottom: 8 }}>欢迎回来</Title>
          <Text type="secondary">登录您的直播营销账户</Text>
        </div>
        
        <Form
          name="login_form"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          size="large"
          layout="vertical"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名!' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="用户名" 
            />
          </Form.Item>
          
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>
          
          <Form.Item>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Form.Item name="remember" valuePropName="checked" noStyle>
                <Checkbox>记住我</Checkbox>
              </Form.Item>
              <Link href="/forgot-password">
                忘记密码?
              </Link>
            </div>
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              style={{ width: '100%' }}
              loading={loading}
            >
              登录
            </Button>
          </Form.Item>
          
          <Divider plain>或者</Divider>
          
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">还没有账户? </Text>
            <Link href="/register">
              立即注册
            </Link>
          </div>
          
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <Link href="/">
              <Button type="link">以游客身份继续</Button>
            </Link>
          </div>
        </Form>
      </Card>
    </div>
  );
}
