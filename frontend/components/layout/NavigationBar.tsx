'use client';

import React from 'react';
import Link from 'next/link';
import { Search, User } from 'lucide-react';
import { useAuth } from '@/app/contexts/AuthContext';

export default function NavigationBar() {
  const { user, logout } = useAuth();

  return (
    <header className="h-14 sm:h-16 border-b border-border bg-white/80 backdrop-blur-md sticky top-0 z-50 flex items-center justify-between px-4 sm:px-6 transition-all">
      {}
      <div className="flex-1 flex items-center">
        <div className="bg-zinc-100 rounded-full px-4 py-1.5 text-sm w-full max-w-[200px] sm:max-w-[240px] md:max-w-96 flex items-center text-zinc-500 focus-within:ring-2 ring-zinc-200 transition-all">
          <Search className="w-4 h-4 mr-2.5 text-zinc-400 shrink-0" />
          <input
            type="text"
            placeholder="Tìm kiếm"
            className="bg-transparent border-none outline-none w-full text-zinc-900 placeholder:text-zinc-500"
          />
        </div>
      </div>

      {}
      <div className="flex items-center justify-end gap-2 sm:gap-3 flex-shrink-0">
        {user ? (
          <div className="flex items-center gap-3 sm:gap-4">
            <span className="text-sm font-medium text-zinc-700 hidden sm:inline-block">
              {user.username || user.full_name || 'User'}
            </span>
            <button
              onClick={logout}
              className="text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors"
            >
              Đăng xuất
            </button>
            <div className="h-8 w-8 rounded-full bg-zinc-100 flex items-center justify-center border border-zinc-200 ">
              <User className="w-4 h-4 text-zinc-500" />
            </div>
          </div>
        ) : (
          <>
            <Link
              href="/login"
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors px-3 py-1.5 rounded-sm hover:bg-zinc-100"
            >
              Đăng nhập
            </Link>
            <Link
              href="/register"
              className="text-sm font-medium bg-zinc-900 text-white hover:bg-zinc-800 transition-all active:scale-95 px-4 py-1.5 rounded-full "
            >
              Đăng ký
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
