"use client";
import React, { createContext, useContext, useState, useEffect } from "react";
const Theme = createContext(undefined);
export function ThemeProvider({ children }) {
    const [theme, setThemeState] = useState("light");
    useEffect(() => {
        const saved = localStorage.getItem("doclib_theme");
        if (saved && (saved === "light" || saved === "dark" || saved === "gray")) {
            setThemeState(saved);
            document.documentElement.classList.add(saved);
        }
        else {
            const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
            const systemTheme = isDark ? "dark" : "light";
            setThemeState(systemTheme);
            document.documentElement.classList.add(systemTheme);
        }
    }, []);
    const setTheme = (newTheme) => {
        document.documentElement.classList.remove(theme);
        setThemeState(newTheme);
        document.documentElement.classList.add(newTheme);
        localStorage.setItem("doclib_theme", newTheme);
    };
    return (<Theme.Provider value={{ theme, setTheme }}>{children}</Theme.Provider>);
}
export function useTheme() {
    const context = useContext(Theme);
    if (context === undefined) {
        throw new Error("useTheme phải được sử dụng bên trong ThemeProvider");
    }
    return context;
}
