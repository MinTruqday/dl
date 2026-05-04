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
      <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-3 max-w-md w-full sm:w-[400px] font-sans pointer-events-none">
        {toasts.map((t) => {
          let typeStyles = "text-black";
          if (t.type === "error") typeStyles = "text-red-600 font-bold";
          if (t.type === "success") typeStyles = "text-green-600";

          return (
            <div
              key={t.id}
              className={`border-l-[6px] border-l-black border border-zinc-200 p-5 text-sm font-semibold bg-white animate-in slide-in-from-right-8 fade-in pointer-events-auto ${typeStyles}`}
            >
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1">
                  <p className="leading-relaxed font-bold tracking-tight">
                    {t.message}
                  </p>
                </div>
                <button
                  onClick={() => removeToast(t.id)}
                  className="opacity-40 transition-opacity p-1 -mt-1 -mr-1 hover:opacity-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
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
