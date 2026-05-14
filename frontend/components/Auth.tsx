"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";

const protectedRoutes: Record<string, string[]> = {
  "/sang-tac": ["author", "admin"],
  "/van-hanh": ["admin"],
  "/ho-so": ["reader", "author", "admin"],
  "/vi-tien": ["reader", "author", "admin"],
  "/nhat-ky": ["moderator", "admin"],
  "/thu-thap": ["admin"],
  "/khoi-tao": ["author", "admin", "moderator"],
  "/phan-tich": ["author", "admin"],
  "/tai-nguyen": ["author", "admin"],
  "/cong-tac": ["author", "admin"],
  "/ma-giam-gia": ["author", "admin"],
  "/thu-vien": ["author", "admin"],
  "/rut-tien": ["author", "admin"],
  "/upload": ["author", "admin"],
  "/quan-ly-nguoi-dung": ["admin"],
  "/bao-cao": ["admin", "moderator"],
  "/tac-gia-tiem-nang": ["admin", "moderator"],
  "/system": ["admin"],
};

export default function Auth({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoading) return;

    const basePath = "/" + pathname.split("/")[1];

    if (protectedRoutes[basePath]) {
      if (!isAuthenticated) {
        router.push("/dang-nhap");
        return;
      }

      const allowedRoles = protectedRoutes[basePath];
      if (user && user.role && !allowedRoles.includes(user.role)) {
        router.push("/");
      }
    }
  }, [isLoading, isAuthenticated, user, pathname, router]);

  return <>{children}</>;
}
