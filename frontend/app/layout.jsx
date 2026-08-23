import { Manrope } from "next/font/google";
import "katex/dist/katex.min.css";
import "./globals.css";
const manrope = Manrope({
  subsets: ["latin", "vietnamese"],
  variable: "--font-sans",
  display: "swap",
});
export const metadata = {
  title: "Nền tảng kiểm định bài đánh giá",
  description: "Soạn thảo kiểm định và hiệu chỉnh bài đánh giá bằng bằng chứng thực nghiệm",
};
import { AuthProvider } from "@/features/authentication/contexts/AuthContext";
import { ToastProvider } from "@/shared/contexts/ToastContext";
import { AnnouncementProvider } from "@/shared/contexts/AnnouncementContext";
import { ChunkRecovery } from "@/shared/components/common/ChunkRecovery";
export default function RootLayout({ children }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className={`${manrope.variable} min-h-[100dvh] font-sans`}>
        <ChunkRecovery />
        <AuthProvider>
          <ToastProvider>
            <AnnouncementProvider>{children}</AnnouncementProvider>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
