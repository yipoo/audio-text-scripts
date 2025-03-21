'use client';

import React, { useState } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space, theme } from 'antd';
import { 
  MenuFoldOutlined, 
  MenuUnfoldOutlined, 
  HomeOutlined, 
  HistoryOutlined, 
  SoundOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  OrderedListOutlined,
  DashboardOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '../../contexts/AuthContext';

const { Header, Sider, Content, Footer } = Layout;

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const { token } = theme.useToken();
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleMenuClick = (e: { key: string }) => {
    if (e.key === 'logout') {
      logout();
      router.push('/login');
    } else if (e.key === 'profile') {
      router.push('/profile');
    } else if (e.key === 'settings') {
      router.push('/settings');
    }
  };

  const userDropdownItems = {
    items: [
      {
        key: 'profile',
        icon: <UserOutlined />,
        label: '个人资料',
      },
      {
        key: 'settings',
        icon: <SettingOutlined />,
        label: '设置',
      },
      {
        type: 'divider',
      },
      {
        key: 'logout',
        icon: <LogoutOutlined />,
        label: '退出登录',
      },
    ],
    onClick: handleMenuClick,
  };

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link href="/">首页</Link>,
    },
    // {
    //   key: '/recordings',
    //   icon: <SoundOutlined />,
    //   label: <Link href="/recordings">录音文件</Link>,
    // },
    {
      key: '/jobs',
      icon: <OrderedListOutlined />,
      label: <Link href="/jobs">任务列表</Link>,
    },
    {
      key: '/scripts',
      icon: <FileTextOutlined />,
      label: <Link href="/scripts">脚本列表</Link>,
    },
    {
      key: '/status',
      icon: <DashboardOutlined />,
      label: <Link href="/status">服务状态</Link>,
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
        <Sider 
          trigger={null} 
          collapsible 
          collapsed={collapsed}
          theme="light"
          style={{
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
            zIndex: 10
          }}
        >
          <div style={{ 
            height: '64px', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: collapsed ? 'center' : 'flex-start',
            padding: collapsed ? '0' : '0 16px',
            color: token.colorPrimary,
            fontWeight: 'bold',
            fontSize: '18px'
          }}>
            {!collapsed && '直播内容生态'}
          </div>
          <Menu
            theme="light"
            mode="inline"
            selectedKeys={[pathname]}
            items={menuItems}
          />
        </Sider>
        <Layout>
          <Header style={{ 
            padding: '0 16px', 
            background: token.colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0, 0, 0, 0.1)'
          }}>
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
            />
            <div>
              {user ? (
                <Dropdown menu={userDropdownItems} placement="bottomRight">
                  <Space style={{ cursor: 'pointer' }}>
                    <Avatar src={user.avatar} icon={<UserOutlined />} />
                    <span>{user.username}</span>
                  </Space>
                </Dropdown>
              ) : (
                <Space>
                  <Link href="/login">
                    <Button type="link">登录</Button>
                  </Link>
                  <Link href="/register">
                    <Button type="primary">注册</Button>
                  </Link>
                </Space>
              )}
            </div>
          </Header>
          <Content style={{ 
            margin: '24px 16px', 
            padding: 24, 
            background: token.colorBgContainer,
            borderRadius: token.borderRadius,
            minHeight: 280
          }}>
            {children}
          </Content>
          <Footer style={{ textAlign: 'center' }}>
            短视频营销软件 {new Date().getFullYear()} 版权所有
          </Footer>
        </Layout>
      </Layout>
  );
}
