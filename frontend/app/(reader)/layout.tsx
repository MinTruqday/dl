import AppShell from '@/app/components/AppShell'

export default function ReaderLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      {children}
    </AppShell>
  )
}
