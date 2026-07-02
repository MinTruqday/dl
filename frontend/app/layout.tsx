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
import { Theme } from "@/components/ThemeProvider";
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
          <Theme
            attribute="class"
            defaultTheme="light"
            enableSystem
            disableTransitionOnChange
          >
            <ToastProvider>
              <AnnouncementProvider>{children}</AnnouncementProvider>
            </ToastProvider>
          </Theme>
        </AuthProvider>
      </body>
    </html>
  );
}
