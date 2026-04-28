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
      <div className="fixed bottom-4 left-4 z-[9999] flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`
              flex items-center gap-3 px-5 py-4 rounded-sm border shadow-2xl pointer-events-auto
              transition-all duration-300 animate-in slide-in-from-left-8 fade-in
              ${t.type === 'success' ? 'bg-white border-zinc-900 text-zinc-900' : 
                t.type === 'error' ? 'bg-white border-zinc-900 text-zinc-900 font-bold' : 
                'bg-zinc-900 border-zinc-900 text-white'}
            `}
          >
            {t.type === 'success' && <CheckCircle className="w-5 h-5 text-green-600" />}
            {t.type === 'error' && <XCircle className="w-5 h-5 text-red-600" />}
            {t.type === 'info' && <Info className="w-5 h-5 text-zinc-400" />}
            <p className="text-sm tracking-tight">{t.message}</p>
            <button
              onClick={() => removeToast(t.id)}
              className="ml-auto opacity-50 hover:opacity-100 transition-opacity p-1"
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
