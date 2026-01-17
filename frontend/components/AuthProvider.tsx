'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '@/types/api';

interface AuthContextType {
  user: User | null;
  userId: number | null;
  login: (userId: number, username: string, email: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [userId, setUserId] = useState<number | null>(null);

  useEffect(() => {
    // Load from localStorage
    const savedUserId = localStorage.getItem('userId');
    const savedUsername = localStorage.getItem('username');
    const savedEmail = localStorage.getItem('email');

    if (savedUserId && savedUsername && savedEmail) {
      setUserId(parseInt(savedUserId));
      setUser({
        id: parseInt(savedUserId),
        username: savedUsername,
        email: savedEmail,
        is_active: true,
        created_at: new Date().toISOString(),
      });
    }
  }, []);

  const login = (userId: number, username: string, email: string) => {
    localStorage.setItem('userId', userId.toString());
    localStorage.setItem('username', username);
    localStorage.setItem('email', email);
    setUserId(userId);
    setUser({
      id: userId,
      username,
      email,
      is_active: true,
      created_at: new Date().toISOString(),
    });
  };

  const logout = () => {
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    localStorage.removeItem('email');
    setUserId(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, userId, login, logout, isAuthenticated: !!userId }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
