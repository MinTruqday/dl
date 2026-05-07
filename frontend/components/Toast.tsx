"use client";

import { CheckCircle, XCircle, X } from "lucide-react";

export interface ToastProps {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

export function ToastContainer({
  toasts,
  removeToast,
}: {
  toasts: ToastProps[];
  removeToast: (id: string) => void;
}) {
  return (
    <div className="fixed bottom-4 left-4 !z-[2147483647] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 px-4 py-3 border text-sm font-medium animate-in slide-in-from-left-8 ${
            t.type === "success"
              ? "bg-white border-black text-black"
              : t.type === "error"
                ? "bg-white border-black text-black font-bold"
                : "bg-black border-black text-white"
          }`}
        >
          {t.type === "success" && <CheckCircle className="w-5 h-5" />}
          {t.type === "error" && <XCircle className="w-5 h-5" />}
          <p>{t.message}</p>
          <button
            onClick={() => removeToast(t.id)}
            className="ml-auto opacity-70 transition-opacity"
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
