"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

type ThemeType = "light" | "dark" | "gray";

interface ThemeProps {
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
}

const Theme = createContext<ThemeProps | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeType>("light");

  useEffect(() => {
    const saved = localStorage.getItem("doclib_theme") as ThemeType;
    if (saved && (saved === "light" || saved === "dark" || saved === "gray")) {
      setThemeState(saved);
      document.documentElement.classList.add(saved);
    } else {
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      const systemTheme = isDark ? "dark" : "light";
      setThemeState(systemTheme);
      document.documentElement.classList.add(systemTheme);
    }
  }, []);

  const setTheme = (newTheme: ThemeType) => {
    document.documentElement.classList.remove(theme);
    setThemeState(newTheme);
    document.documentElement.classList.add(newTheme);
    localStorage.setItem("doclib_theme", newTheme);
  };

  return (
    <Theme.Provider value={{ theme, setTheme }}>
      {children}
    </Theme.Provider>
  );
}

export function useTheme() {
  const context = useContext(Theme);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
