"use client";
import React, { createContext, useCallback, useContext, useEffect, useState, } from "react";
import { getUserMe, getUserFromToken, getToken, removeToken, logoutAPI, } from "@/features/authentication/services/session.service";
import { useRouter } from "next/navigation";
const AuthContext = createContext(undefined);
export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const clearAuth = useCallback(() => {
        removeToken();
        document.cookie = "token=; path=/; max-age=0; SameSite=Lax";
        document.cookie = "role=; path=/; max-age=0; SameSite=Lax";
        setUser(null);
    }, []);
    const fetchUser = useCallback(async () => {
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
            }
            else {
                clearAuth();
            }
        }
        catch (_a) {
            const sessionUser = getUserFromToken(token);
            if (sessionUser) {
                setUser(sessionUser);
                document.cookie = `token=${token}; path=/; max-age=604800; SameSite=Lax`;
                document.cookie = `role=${sessionUser.role}; path=/; max-age=604800; SameSite=Lax`;
            }
        }
        finally {
            setIsLoading(false);
        }
    }, [clearAuth]);
    useEffect(() => {
        void fetchUser();
    }, [fetchUser]);
    const loginState = async (token) => {
        localStorage.setItem("doclib_token", token);
        document.cookie = `token=${token}; path=/; max-age=604800; SameSite=Lax`;
        await fetchUser();
    };
    const logoutState = async () => {
        try {
            await logoutAPI();
        }
        finally {
            clearAuth();
            router.push("/dang-nhap");
        }
    };
    return (<AuthContext.Provider value={{
            user,
            isAuthenticated: !!user,
            isLoading,
            loginState,
            logoutState,
            refreshUser: fetchUser,
        }}>
      {children}
    </AuthContext.Provider>);
}
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth passed outside of AuthProvider");
    }
    return context;
};
