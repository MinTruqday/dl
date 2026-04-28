import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DocLib',
  description: 'Nền tảng chia sẻ eBook',
}

import { AuthProvider } from './contexts/AuthContext'
import { ThemeProvider } from './components/ThemeProvider'
import { ToastProvider } from './contexts/ToastContext'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className={`${inter.className} min-h-screen bg-white`}>
        <AuthProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="light"
            enableSystem
            disableTransitionOnChange
          >
            <ToastProvider>
              {children}
            </ToastProvider>
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
