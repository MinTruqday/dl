import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-sans',
})

export const metadata: Metadata = {
  title: 'DocLib',
  description: 'Hệ thống quản lý tài liệu thông minh',
}

import { AuthProvider } from '@/contexts/AuthContext'
import { Theme } from '@/components/Theme'
import { ToastProvider } from '@/contexts/ToastContext'
import { NotificationProvider } from '@/contexts/NotificationContext'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
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
              <NotificationProvider>
                {children}
              </NotificationProvider>
            </ToastProvider>
          </Theme>
        </AuthProvider>
      </body>
    </html>
  )
}
