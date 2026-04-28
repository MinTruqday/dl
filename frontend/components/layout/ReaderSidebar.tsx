import Link from 'next/link'

export default function ReaderSidebar() {
  return (
    <aside className="w-64 border-r border-gray-200 bg-gray-50 h-screen p-4">
      <div className="font-bold text-xl mb-8">DocLib</div>
      <nav className="flex flex-col gap-2">
        <Link href="/" className="p-2 hover:bg-white border border-transparent hover:border-gray-200 rounded-md transition-colors">
          Trang chủ
        </Link>
        <Link href="/explore" className="p-2 hover:bg-white border border-transparent hover:border-gray-200 rounded-md transition-colors">
          Khám phá
        </Link>
        <Link href="/library" className="p-2 hover:bg-white border border-transparent hover:border-gray-200 rounded-md transition-colors">
          Tủ sách
        </Link>
      </nav>
    </aside>
  )
}
