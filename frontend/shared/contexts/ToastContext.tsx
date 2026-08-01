"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from "react";
import { X, AlertCircle, CheckCircle2, Info } from "lucide-react";

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
        <div className="fixed top-24 right-4 sm:right-6 z-[500] flex flex-col items-end gap-3 pointer-events-none font-sans">
          {toasts.map((t) => {
            let icon = null;
            if (t.type === "error") {
              icon = <AlertCircle className="w-4 h-4 text-danger" />;
            } else if (t.type === "success") {
              icon = <CheckCircle2 className="w-4 h-4 text-ink" />;
            } else {
              icon = <Info className="w-4 h-4 text-ink" />;
            }

            return (
              <div
                key={t.id}
                className="relative bg-surface border border-border rounded-panel p-4 shadow-lg pointer-events-auto animate-in fade-in slide-in-from-bottom-4 [transition-duration:220ms] ease-out min-w-[300px] max-w-[400px] flex items-center gap-3"
              >
                <div className={`shrink-0 flex items-center justify-center w-8 h-8 rounded-full ${t.type === "error" ? "bg-danger-soft text-danger" : t.type === "success" ? "bg-brand-soft text-brand" : "bg-surface-quiet text-ink"}`}>
                  {icon}
                </div>

                <div className="flex-1 min-w-0 flex items-center">
                  <p className="text-sm font-medium text-ink break-words">
                    {t.message}
                  </p>
                </div>

                <button
                  type="button"
                  aria-label="Đóng thông báo"
                  onClick={() => removeToast(t.id)}
                  className="shrink-0 flex items-center justify-center w-8 h-8 cursor-pointer rounded-xl text-ink-faint hover:text-ink hover:bg-surface-quiet transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
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
