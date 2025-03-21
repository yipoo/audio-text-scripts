import type { Metadata } from "next";
import "./globals.css";
import { AntdRegistry } from '@ant-design/nextjs-registry';
import { App as AntdApp, ConfigProvider } from 'antd';
import { AuthProvider } from '../contexts/AuthContext';
import { geist } from './fonts';

export const metadata: Metadata = {
  title: "直播升级营销软件",
  description: "录制抖音直播语音，使用AI生成多份营销话术",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${geist.variable} antialiased`}
      >
        <AntdRegistry>
          <ConfigProvider>
            <AntdApp>
              <AuthProvider>
                {children}
              </AuthProvider>
            </AntdApp>
          </ConfigProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
