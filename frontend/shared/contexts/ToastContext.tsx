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
              icon = <AlertCircle className="size-4" />;
            } else if (t.type === "success") {
              icon = <CheckCircle2 className="size-4" />;
            } else {
              icon = <Info className="size-4" />;
            }

            return (
              <div
                key={t.id}
                className="pointer-events-auto relative flex min-w-[280px] max-w-[400px] items-center gap-3 rounded-[var(--radius-panel)] border border-[var(--border)] bg-[var(--surface)] p-3 shadow-[0_18px_48px_rgba(32,32,30,0.14)]"
              >
                <div className={`flex size-8 shrink-0 items-center justify-center rounded-[var(--radius-control)] ${t.type === "error" ? "bg-[var(--danger-soft)] text-[var(--danger)]" : t.type === "success" ? "bg-[var(--success-soft)] text-[var(--success)]" : "bg-[var(--surface-quiet)] text-[var(--ink)]"}`}>
                  {icon}
                </div>

                <div className="flex-1 min-w-0 flex items-center">
                  <p className="break-words text-[14px] font-medium text-[var(--ink)]">
                    {t.message}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => removeToast(t.id)}
                  aria-label="Đóng thông báo"
                  className="flex size-8 shrink-0 items-center justify-center rounded-[var(--radius-control)] text-[var(--ink-muted)] hover:bg-[var(--surface-quiet)] hover:text-[var(--ink)]"
                >
                  <X aria-hidden="true" className="size-4" />
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
