'use client';

import { useAuth } from '@/app/contexts/AuthContext';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';

const protectedRoutes: Record<string, string[]> = {
  '/studio': ['author', 'admin'],
  '/admin': ['admin'],
  '/profile': ['reader', 'author', 'admin'],
  '/wallet': ['reader', 'author', 'admin'],
};

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoading) return;

    const basePath = '/' + pathname.split('/')[1];

    if (protectedRoutes[basePath]) {
      if (!isAuthenticated) {
        router.push('/login');
        return;
      }
      
      const allowedRoles = protectedRoutes[basePath];
      if (user && user.role && !allowedRoles.includes(user.role)) {
        router.push('/');
      }
    }
  }, [isLoading, isAuthenticated, user, pathname, router]);

  return <>{children}</>;
}
