import Link from 'next/link'

export default function AuthorSidebar() {
  return (
    <aside className="w-64 border-r border-gray-200 bg-black text-white h-screen p-4">
      <div className="font-bold text-xl mb-8">DocLib Studio</div>
      <nav className="flex flex-col gap-2">
        <Link href="/studio" className="p-2 hover:bg-gray-800 border border-transparent hover:border-gray-700 rounded-md transition-colors">
          Bảng điều khiển
        </Link>
        <Link href="/studio/upload" className="p-2 hover:bg-gray-800 border border-transparent hover:border-gray-700 rounded-md transition-colors">
          Đăng bài mới
        </Link>
        <Link href="/studio/analytics" className="p-2 hover:bg-gray-800 border border-transparent hover:border-gray-700 rounded-md transition-colors">
          Thống kê
        </Link>
      </nav>
    </aside>
  )
}
