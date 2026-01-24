import React, { createContext, useContext, useEffect, useState } from "react";

type User = {
  id: number;
  email: string;
  full_name?: string;
  phone_number?: string;
  role?: string;
};

type AuthContextType = {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: (tokenArg?: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));

  useEffect(() => {
    if (token) {
      refreshUser();
    }
  }, [token]);

  const refreshUser = async (tokenArg?: string) => {
    const tok = tokenArg ?? token;
    if (!tok) return;
    try {
      const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      const res = await fetch(`${base}/auth/me`, {
        headers: { Authorization: `Bearer ${tok}` },
        credentials: "include",
      });
      if (!res.ok) {
        setUser(null);
        setToken(null);
        localStorage.removeItem("token");
        return;
      }
      const data = await res.json();
      setUser(data);
    } catch (e) {
      setUser(null);
      setToken(null);
      localStorage.removeItem("token");
    }
  };

  const login = async (email: string, password: string) => {
    const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    const res = await fetch(`${base}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Login failed");
    const payload = await res.json();
    const t = payload.access_token;
    setToken(t);
    localStorage.setItem("token", t);
    await refreshUser(t);
  };

  const logout = () => {
    const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    fetch(`${base}/auth/logout`, { method: "POST", credentials: "include" }).catch(() => {});
    setUser(null);
    setToken(null);
    localStorage.removeItem("token");
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
