import React from "react";
import AuthGuard from "@/app/components/AuthGuard";
import AppShell from "@/app/components/AppShell";
import AiChatPanel from "@/app/components/AiChatPanel";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <AppShell>
        {children}
      </AppShell>
    </AuthGuard>
  );
}
