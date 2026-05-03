"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { X } from "lucide-react";

export interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

interface ToastContextType {
  showToast: (message: string, type?: "success" | "error" | "info") => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback(
    (message: string, type: "success" | "error" | "info" = "info") => {
      const id = Math.random().toString(36).substring(2, 9);
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    },
    [],
  );

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      <div
        style={{
          position: "fixed",
          top: "80px",
          right: "30px",
          zIndex: 9999,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-end",
          gap: "16px",
          pointerEvents: "none",
          fontFamily: "sans-serif",
        }}
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            style={{ borderLeft: "6px solid black" }}
            className={`
 bg-white p-4 flex items-center gap-10 animate-in slide-in-from-right-8 fade-in pointer-events-auto whitespace-nowrap min-w-max shadow-none
 ${
   t.type === "error"
     ? "text-red-600 font-bold"
     : t.type === "success"
       ? "text-green-600 font-bold"
       : "text-black"
 }
 `}
          >
            <div className="text-base leading-none tracking-tight">
              {t.message}
            </div>
            <button
              onClick={() => removeToast(t.id)}
              className="opacity-20 p-1 -mr-1 flex items-center justify-center"
            >
              <X size={18} />
            </button>
          </div>
        ))}
      </div>
      {children}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
