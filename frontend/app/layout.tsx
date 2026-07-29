import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  subsets: ["latin", "vietnamese"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "DocLib",
  description: "Soạn thảo cộng tác và xuất bản tài liệu",
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
    <html lang="vi">
      <body className={`${manrope.variable} min-h-[100dvh]`}>
        <AuthProvider>
          <ToastProvider>
            <AnnouncementProvider>{children}</AnnouncementProvider>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
