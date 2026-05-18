"use client";
import React, { createContext, useContext, useEffect, useState } from "react";
import { getUserMe, getToken, removeToken } from "@/services/authentication.service";
import { useRouter, usePathname } from "next/navigation";

interface User {
  _id: string;
  email: string;
  full_name: string;
  slug: string;
  role: string;
  avatar_url?: string;
  bio?: string;
  wallet_balance: number;
}

interface AuthProps {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginState: (token: string) => Promise<void>;
  logoutState: () => void;
}

const Auth = createContext<AuthProps | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const fetchUser = async () => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    try {
      const data = await getUserMe();
      if (data) {
        setUser(data);
        document.cookie = `token=${token}; path=/; max-age=604800; SameSite=Lax`;
        document.cookie = `role=${data.role}; path=/; max-age=604800; SameSite=Lax`;
      } else {
        clearAuth();
      }
    } catch (error) {
      clearAuth();
    }
    setIsLoading(false);
  };

  useEffect(() => {
    fetchUser();
  }, [pathname]);

  const loginState = async (token: string) => {
    localStorage.setItem("doclib_token", token);
    document.cookie = `token=${token}; path=/; max-age=604800; SameSite=Lax`;
    await fetchUser();
  };

  const clearAuth = () => {
    removeToken();
    setUser(null);
  };

  const logoutState = () => {
    clearAuth();
    router.push("/dang-nhap");
  };

  return (
    <Auth.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        loginState,
        logoutState,
      }}
    >
      {children}
    </Auth.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(Auth);
  if (!context) {
    throw new Error("useAuth passed outside of AuthProvider");
  }
  return context;
};
