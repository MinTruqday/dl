"use client";
import { CheckCircle, XCircle, X } from "lucide-react";
export function ToastContainer({ toasts, removeToast }) {
  return (
    <div className="fixed bottom-4 left-4 !z-[2147483647] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 px-4 py-3 border text-sm font-medium animate-in slide-in-from-left-8 ${
            t.type === "success"
              ? "bg-white border-ink text-ink"
              : t.type === "error"
                ? "bg-white border-ink text-ink font-bold"
                : "bg-ink border-ink text-white"
          }`}
        >
          {t.type === "success" && <CheckCircle className="w-5 h-5" />}
          {t.type === "error" && <XCircle className="w-5 h-5" />}
          <p>{t.message}</p>
          <button
            type="button"
            aria-label="Đóng thông báo"
            onClick={() => removeToast(t.id)}
            className="ml-auto opacity-70"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
export function useToast() {
  import("react").then((React) => {});
}
