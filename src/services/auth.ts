import { useState, useEffect } from 'react';

// 用户类型
export interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
}

// 模拟用户数据
const MOCK_USERS = [
  {
    id: '1',
    username: 'demo',
    password: 'demo123',
    email: 'demo@example.com',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=demo'
  },
  {
    id: '2',
    username: 'admin',
    password: 'admin123',
    email: 'admin@example.com',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin'
  }
];

// 登录函数
export const login = async (username: string, password: string): Promise<User> => {
  // 模拟API请求延迟
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 查找用户
  const user = MOCK_USERS.find(
    u => u.username === username && u.password === password
  );
  
  if (!user) {
    throw new Error('用户名或密码错误');
  }
  
  // 存储用户信息到localStorage
  const userData: User = {
    id: user.id,
    username: user.username,
    email: user.email,
    avatar: user.avatar
  };
  
  localStorage.setItem('user', JSON.stringify(userData));
  
  return userData;
};

// 注册函数
export const register = async (
  username: string, 
  email: string, 
  password: string
): Promise<User> => {
  // 模拟API请求延迟
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 检查用户名是否已存在
  if (MOCK_USERS.some(u => u.username === username)) {
    throw new Error('用户名已存在');
  }
  
  // 检查邮箱是否已存在
  if (MOCK_USERS.some(u => u.email === email)) {
    throw new Error('邮箱已存在');
  }
  
  // 创建新用户
  const newUser = {
    id: `${MOCK_USERS.length + 1}`,
    username,
    password,
    email,
    avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${username}`
  };
  
  // 在实际应用中，这里会调用API将用户添加到数据库
  MOCK_USERS.push(newUser);
  
  // 存储用户信息到localStorage
  const userData: User = {
    id: newUser.id,
    username: newUser.username,
    email: newUser.email,
    avatar: newUser.avatar
  };
  
  localStorage.setItem('user', JSON.stringify(userData));
  
  return userData;
};

// 登出函数
export const logout = (): void => {
  localStorage.removeItem('user');
};

// 获取当前用户
export const getCurrentUser = (): User | null => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr) as User;
  } catch (error) {
    console.error('解析用户数据失败:', error);
    return null;
  }
};

// 自定义Hook: 使用当前用户
export const useCurrentUser = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // 在客户端渲染时获取用户
    if (typeof window !== 'undefined') {
      setUser(getCurrentUser());
      setLoading(false);
    }
  }, []);
  
  return { user, loading, setUser };
};
