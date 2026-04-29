'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, XCircle, Info, X } from 'lucide-react';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface ToastContextType {
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed top-12 right-12 z-[9999] flex flex-col gap-5 pointer-events-none max-w-md w-full sm:w-[450px]">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`
              flex items-center gap-6 px-8 py-6 border border-zinc-100 border-l-[8px] border-l-black bg-white pointer-events-auto
              transition-all duration-500 animate-in slide-in-from-right-12 fade-in
              ${t.type === 'success' ? 'text-emerald-600' : 
                t.type === 'error' ? 'text-rose-600' : 
                'text-amber-500'}
            `}
          >
            <div className="shrink-0">
              {t.type === 'success' && <CheckCircle className="w-6 h-6" />}
              {t.type === 'error' && <XCircle className="w-6 h-6" />}
              {t.type === 'info' && <Info className="w-6 h-6" />}
            </div>
            <p className="text-base font-bold tracking-tight flex-1 selection:bg-black selection:text-white leading-tight">
              {t.message}
            </p>
            <button
              onClick={() => removeToast(t.id)}
              className="text-zinc-300 hover:text-black transition-all p-1 active:scale-90"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
