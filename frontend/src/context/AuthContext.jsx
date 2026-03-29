import { createContext, useContext, useMemo, useState } from 'react';
import { authApi } from '../api/endpoints';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('estatex_token'));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('estatex_user');
    return raw ? JSON.parse(raw) : null;
  });

  const login = async (payload) => {
    const { data } = await authApi.login(payload);
    localStorage.setItem('estatex_token', data.access_token);
    localStorage.setItem('estatex_user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data;
  };

  const register = async (payload) => {
    const { data } = await authApi.register(payload);
    localStorage.setItem('estatex_token', data.access_token);
    localStorage.setItem('estatex_user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data;
  };

  const updateWallet = async (payload) => {
    const { data } = await authApi.updateWallet(payload);
    localStorage.setItem('estatex_user', JSON.stringify(data));
    setUser(data);
    return data;
  };

  const logout = () => {
    localStorage.removeItem('estatex_token');
    localStorage.removeItem('estatex_user');
    setToken(null);
    setUser(null);
  };

  const value = useMemo(
    () => ({ token, user, isAuthenticated: Boolean(token), login, register, logout, updateWallet }),
    [token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
