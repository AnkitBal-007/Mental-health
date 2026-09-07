import React, { createContext, useContext, useState, useCallback } from 'react';
import { login as apiLogin } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const login = useCallback(async (username, password) => {
    const data = await apiLogin(username, password);
    if (!data?.access_token) throw new Error('No token received');

    // Decode JWT payload (not verified — for display only)
    const payloadB64 = data.access_token.split('.')[1];
    const payload = JSON.parse(atob(payloadB64));

    const userObj = {
      username: payload.sub || username,
      role: payload.role || 'district',
      district: payload.district || null,
      state: payload.state || null,
      token: data.access_token,
    };

    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(userObj));
    setUser(userObj);
    return userObj;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
