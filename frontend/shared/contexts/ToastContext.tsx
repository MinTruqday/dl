"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from "react";
import { X } from "lucide-react";

export interface ToastItem {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

interface ToastProps {
  showToast: (message: string, type?: "success" | "error" | "info") => void;
}

const Toast = createContext<ToastProps | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

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
    <Toast.Provider value={{ showToast }}>
      {children}
      {isClient && (
        <div
          style={{
            position: "fixed",
            top: "80px",
            right: "30px",
            zIndex: 999999,
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-end",
            gap: "16px",
            pointerEvents: "none",
            fontFamily: "sans-serif",
          }}
        >
          {toasts.map((t) => {
            let typeStyles = "text-black";
            if (t.type === "error") typeStyles = "text-red-600 font-bold";
            if (t.type === "success") typeStyles = "text-green-600";

            return (
              <div
                key={t.id}
                className={`relative border border-zinc-200 p-5 text-sm font-semibold bg-white animate-in slide-in-from-right-8 fade-in pointer-events-auto shadow-sm ${typeStyles}`}
              >
                <div
                  className="absolute w-1 bg-black"
                  style={{ top: "-1px", bottom: "-1px", left: "-1px" }}
                />
                <div className="flex justify-between items-center gap-6 whitespace-nowrap min-w-max">
                  <div className="flex-1 pl-2">
                    <p className="leading-relaxed font-bold tracking-tight">
                      {t.message}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      removeToast(t.id);
                    }}
                    className="opacity-40 hover:opacity-100 transition-opacity p-2 cursor-pointer rounded-none flex items-center justify-center"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Toast.Provider>
  );
}

export function useToast() {
  const context = useContext(Toast);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
