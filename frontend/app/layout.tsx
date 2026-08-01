import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  subsets: ["latin", "vietnamese"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "DocLib",
  description:
    "Đọc, quản lý và cộng tác trên tài liệu trong một không gian làm việc",
};

import { AuthProvider } from "@/features/authentication/contexts/AuthContext";
import { ToastProvider } from "@/shared/contexts/ToastContext";
import { AnnouncementProvider } from "@/shared/contexts/AnnouncementContext";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className={`${manrope.variable} min-h-[100dvh] font-sans`}>
        <AuthProvider>
          <ToastProvider>
            <AnnouncementProvider>{children}</AnnouncementProvider>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
