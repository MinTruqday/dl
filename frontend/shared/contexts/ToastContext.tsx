"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

export type ToastItem = {
  id: string;
  message: string;
  type: "success" | "error" | "info";
};

type ToastContextValue = {
  showToast: (message: string, type?: ToastItem["type"]) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const removeToast = useCallback((id: string) => {
    setToasts((items) => items.filter((item) => item.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, type: ToastItem["type"] = "info") => {
      const id = crypto.randomUUID();
      setToasts((items) => [...items, { id, message, type }]);
      window.setTimeout(() => removeToast(id), 4000);
    },
    [removeToast],
  );

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {mounted && toasts.length > 0 && (
        <div
          className="pointer-events-none fixed bottom-5 right-4 z-[2500] flex w-[min(380px,calc(100vw-2rem))] flex-col gap-2 sm:right-6"
          aria-live="polite"
        >
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className={`pointer-events-auto flex items-start gap-4 border bg-surface px-4 py-3 shadow-[0_12px_36px_rgba(32,32,30,0.12)] ${toast.type === "error" ? "border-danger/40" : toast.type === "success" ? "border-brand/40" : "border-border-strong"}`}
              role={toast.type === "error" ? "alert" : "status"}
            >
              <p className="min-w-0 flex-1 text-[13px] font-medium leading-5 text-ink">
                {toast.message}
              </p>
              <button
                type="button"
                onClick={() => removeToast(toast.id)}
                className="shrink-0 text-[12px] font-semibold text-ink-muted hover:text-ink"
              >
                Đóng
              </button>
            </div>
          ))}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("ToastProvider chưa được khởi tạo");
  return context;
}
