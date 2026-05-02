"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

type Theme = "light" | "dark" | "gray";

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function Theme({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("light");

  useEffect(() => {
    const saved = localStorage.getItem("doclib_theme") as Theme;
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

  const setTheme = (newTheme: Theme) => {
    document.documentElement.classList.remove(theme);
    setThemeState(newTheme);
    document.documentElement.classList.add(newTheme);
    localStorage.setItem("doclib_theme", newTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a Theme");
  }
  return context;
}
