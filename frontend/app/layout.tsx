import "./globals.css";
import React from "react";
import type { Metadata } from "next";
import { Inter } from "next/font/google";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "DocLib | Nền tảng Tri thức Phân tán",
  description: "DocLib là nền tảng tối giản dành cho việc đọc, viết và chia sẻ tài liệu học thuật. Kết nối cộng đồng tri thức thông qua công nghệ AI và hệ thống quản trị minh bạch.",
  keywords: ["tài liệu", "sách số", "tri thức", "học thuật", "AI đọc sách", "viết lách", "DocLib"],
  authors: [{ name: "DocLib Team" }],
  viewport: "width=device-width, initial-scale=1",
  robots: "index, follow",
  openGraph: {
    title: "DocLib | Nền tảng Tri thức Phân tán",
    description: "Khám phá thế giới tri thức với DocLib. Đọc, viết và kết nối.",
    url: "https://doclib.io",
    siteName: "DocLib",
    locale: "vi_VN",
    type: "website",
  },
  icons: {
    icon: "/favicon.ico",
  },
};

import { AuthProvider } from "@/app/contexts/AuthContext";
import { ThemeProvider } from "@/app/contexts/ThemeContext";
import NotificationToast from "@/app/components/NotificationToast";
import AiChatPanel from "@/app/components/AiChatPanel";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className={inter.variable}>
      <body className="font-sans antialiased min-h-screen bg-background text-foreground transition-colors duration-300">
        <AuthProvider>
          <ThemeProvider>
            {children}
            <NotificationToast />
            <AiChatPanel />
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
