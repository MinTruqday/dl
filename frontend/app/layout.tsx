import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "DocLib",
  description: "Hệ thống quản lý tài liệu thông minh",
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
      <body className={`${inter.variable} font-sans min-h-screen bg-white`}>
        <AuthProvider>
          <ToastProvider>
            <AnnouncementProvider>{children}</AnnouncementProvider>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
