"use client";

import { useEffect, useState } from "react";
import { Users, Shield, UserX, UserCheck, Search, Filter, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AdminUserManagement() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Tạm thời sử dụng dữ liệu sạch thay vì tên riêng biệt
    const mockUsers = [
      { id: "1", name: "Quản trị viên", email: "admin@doclib.io", role: "ADMIN", status: "ACTIVE", joined: "2024-01-10" },
      { id: "2", name: "Tác giả Hệ thống", email: "author@doclib.io", role: "AUTHOR", status: "ACTIVE", joined: "2024-02-15" },
      { id: "3", name: "Độc giả 01", email: "reader01@doclib.io", role: "READER", status: "SUSPENDED", joined: "2024-03-20" },
    ];
    setUsers(mockUsers);
    setLoading(false);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b-2 border-black pb-8 mb-12">
        <div>
           <div className="flex items-center gap-3 mb-2">
              <Shield className="w-5 h-5 text-black" />
              <span className="text-[10px] font-bold tracking-widest text-zinc-400">Quản trị hệ thống</span>
           </div>
           <h1 className="text-4xl font-black text-black tracking-tighter">Quản lý người dùng</h1>
        </div>
        <div className="flex gap-4">
           <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input 
                 className="bg-zinc-50 border border-zinc-200 pl-10 pr-4 py-2.5 text-xs font-bold tracking-widest outline-none focus:border-black transition-all min-w-[300px]"
                 placeholder="Tìm kiếm người dùng"
              />
           </div>
           <Button variant="outline" className="text-[10px] font-bold tracking-widest border-black h-11 px-6">
              <Filter className="w-4 h-4 mr-2" /> Lọc
           </Button>
        </div>
      </header>

      <div className="border border-black overflow-hidden">
         <table className="w-full text-left border-collapse">
            <thead>
               <tr className="bg-black text-white text-[10px] font-bold tracking-widest">
                  <th className="px-6 py-4">Người dùng</th>
                  <th className="px-6 py-4">Vai trò</th>
                  <th className="px-6 py-4">Trạng thái</th>
                  <th className="px-6 py-4">Ngày tham gia</th>
                  <th className="px-6 py-4 text-right">Thao tác</th>
               </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
               {users.map((user) => (
                  <tr key={user.id} className="hover:bg-zinc-50 transition-colors group">
                     <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                           <div className="w-10 h-10 bg-zinc-100 border border-zinc-200 flex items-center justify-center font-black text-zinc-400">
                              {user.name[0]}
                           </div>
                           <div>
                              <p className="text-sm font-black tracking-tight">{user.name}</p>
                              <p className="text-[10px] text-zinc-400 font-bold">{user.email}</p>
                           </div>
                        </div>
                     </td>
                     <td className="px-6 py-4">
                        <span className={`text-[9px] font-black tracking-widest px-2 py-1 border ${user.role === 'ADMIN' ? 'bg-black text-white border-black' : 'border-zinc-200 text-zinc-500'}`}>
                           {{ ADMIN: 'Quản trị', AUTHOR: 'Tác giả', READER: 'Độc giả', MODERATOR: 'Kiểm duyệt' }[user.role] || user.role}
                        </span>
                     </td>
                     <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                           <div className={`w-1.5 h-1.5 rounded-none ${user.status === 'ACTIVE' ? 'bg-black' : 'bg-zinc-200'}`} />
                           <span className="text-[10px] font-bold tracking-widest text-zinc-600">{{ ACTIVE: 'Hoạt động', SUSPENDED: 'Đã khóa', BANNED: 'Cấm' }[user.status] || user.status}</span>
                        </div>
                     </td>
                     <td className="px-6 py-4 text-xs font-bold text-zinc-400">
                        {user.joined}
                     </td>
                     <td className="px-6 py-4 text-right">
                        <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                           <button className="p-2 border border-zinc-100 hover:border-black transition-all" title="Khóa tài khoản">
                              <UserX className="w-4 h-4 text-black" />
                           </button>
                           <button className="p-2 border border-zinc-100 hover:border-black transition-all">
                              <MoreVertical className="w-4 h-4 text-zinc-400" />
                           </button>
                        </div>
                     </td>
                  </tr>
               ))}
            </tbody>
         </table>
      </div>
      
      <div className="mt-8 flex justify-between items-center">
         <p className="text-[10px] font-bold tracking-widest text-zinc-400">Hiển thị {users.length} trên tổng số 1,240 người dùng</p>
         <div className="flex gap-2">
            <button className="px-4 py-2 border border-zinc-200 text-[10px] font-bold hover:border-black disabled:opacity-30" disabled>Trước</button>
            <button className="px-4 py-2 border border-black bg-black text-white text-[10px] font-bold">1</button>
            <button className="px-4 py-2 border border-zinc-200 text-[10px] font-bold hover:border-black">2</button>
            <button className="px-4 py-2 border border-zinc-200 text-[10px] font-bold hover:border-black">Tiếp</button>
         </div>
      </div>
    </div>
  );
}
