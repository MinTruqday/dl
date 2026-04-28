import AppShell from '@/app/components/AppShell'

export default function ModeratorLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      {children}
    </AppShell>
  )
}
