"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";

const protectedRoutes: Record<string, string[]> = {
  "/studio": ["author", "admin"],
  "/administration": ["admin"],
  "/profile": ["reader", "author", "admin"],
  "/wallet": ["reader", "author", "admin"],
  "/moderation": ["moderator", "admin"],
  "/create": ["author", "admin"],
  "/analytics": ["author", "admin"],
  "/assets": ["author", "admin"],
  "/collab": ["author", "admin"],
  "/coupon": ["author", "admin"],
  "/library": ["author", "admin"],
  "/payout": ["author", "admin"],
  "/upload": ["author", "admin"],
  "/user": ["admin"],
  "/reports": ["admin", "moderator"],
  "/applications": ["admin", "moderator"],
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
        router.push("/login");
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
