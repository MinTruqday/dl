"use client";

import Workspace from "@/components/Workspace";
import { usePathname } from "next/navigation";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  // Determine if the current route is publicly accessible to guests
  const isPublic = () => {
    if (pathname === "/") return true;
    if (pathname === "/xep-hang") return true;
    if (pathname.startsWith("/author")) return true;
    if (pathname.startsWith("/tim-kiem")) return true;
    
    // /tai-lieu/viewer and /tai-lieu/[slug] details are public, but the workspace list /tai-lieu itself requires auth
    if (pathname.startsWith("/tai-lieu/")) {
      return true;
    }
    
    return false;
  };

  return <Workspace requireAuth={!isPublic()}>{children}</Workspace>;
}
