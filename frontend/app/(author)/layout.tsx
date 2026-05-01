import AppShell from '@/app/components/AppShell'

export default function AuthorLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      {children}
    </AppShell>
  )
}
