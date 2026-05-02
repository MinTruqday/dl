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
              border-l-[6px] p-4 text-sm font-semibold bg-white transition-all duration-500 animate-in slide-in-from-right-12 fade-in font-sans pointer-events-auto flex justify-between items-start gap-4 shadow-sm border-y border-r border-zinc-100
              ${t.type === 'success' ? 'border-l-black text-green-600' : 
                t.type === 'error' ? 'border-l-black text-red-600 font-bold' : 
                'border-l-black text-zinc-900'}
            `}
          >
            <div className="flex-1 min-w-0">
              <div className="leading-relaxed font-medium">
                {t.message}
              </div>
            </div>
            <button
              onClick={() => removeToast(t.id)}
              className="opacity-40 hover:opacity-100 transition-opacity p-1 -mt-1 -mr-1"
            >
              <X className="w-4 h-4" />
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
