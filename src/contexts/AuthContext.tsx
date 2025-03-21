'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, getCurrentUser, login, logout, register } from '../services/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<User>;
  logout: () => void;
  register: (username: string, email: string, password: string) => Promise<User>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 在客户端渲染时获取用户
    if (typeof window !== 'undefined') {
      const currentUser = getCurrentUser();
      setUser(currentUser);
      setLoading(false);
    }
  }, []);

  const handleLogin = async (username: string, password: string) => {
    const loggedInUser = await login(username, password);
    setUser(loggedInUser);
    return loggedInUser;
  };

  const handleLogout = () => {
    logout();
    setUser(null);
  };

  const handleRegister = async (username: string, email: string, password: string) => {
    const newUser = await register(username, email, password);
    setUser(newUser);
    return newUser;
  };

  const value = {
    user,
    loading,
    login: handleLogin,
    logout: handleLogout,
    register: handleRegister
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
