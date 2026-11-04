"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import type { AuthUser } from "@oldpages/shared-types";
import { apiClient } from "../lib/api";
import {
  clearTokens,
  getAccessToken,
  setTokens,
} from "../lib/auth";

type AuthContextType = {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (
    name: string,
    email: string,
    password: string,
  ) => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    apiClient
      .getMe(token)
      .then((me) => {
        setUser({
          id: me.id,
          email: me.email,
          email_verified: me.email_verified,
          status: me.status,
        });
      })
      .catch(() => {
        clearTokens();
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiClient.login({ email, password });
    setTokens(response.tokens.access_token, response.tokens.refresh_token);
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    window.location.href = "/";
  }, []);

  const register = useCallback(
    async (name: string, email: string, password: string) => {
      const response = await apiClient.register({
        display_name: name,
        email,
        password,
        privacy_accepted: true,
        terms_accepted: true,
      });
      setTokens(response.tokens.access_token, response.tokens.refresh_token);
      setUser(response.user);
    },
    [],
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        register,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
