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
              icon = <AlertCircle className="w-4 h-4 text-white" />;
            } else if (t.type === "success") {
              icon = <CheckCircle2 className="w-4 h-4 text-black" />;
            } else {
              icon = <Info className="w-4 h-4 text-black" />;
            }

            return (
              <div
                key={t.id}
                className="relative bg-white border border-zinc-200 rounded-2xl p-4 shadow-xl pointer-events-auto animate-in fade-in slide-in-from-bottom-4 [transition-duration:420ms] ease-out min-w-[300px] max-w-[400px] flex items-center gap-3"
              >
                <div className={`shrink-0 flex items-center justify-center w-8 h-8 rounded-full ${t.type === "error" ? "bg-red-50 text-red-600" : t.type === "success" ? "bg-green-50 text-green-600" : "bg-zinc-100 text-zinc-900"}`}>
                  {icon}
                </div>

                <div className="flex-1 min-w-0 flex items-center">
                  <p className="text-sm font-medium text-zinc-900 break-words">
                    {t.message}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => removeToast(t.id)}
                  className="shrink-0 flex items-center justify-center w-8 h-8 cursor-pointer rounded-xl text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 transition-colors"
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
