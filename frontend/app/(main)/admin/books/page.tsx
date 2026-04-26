"use client";

import React, { useState, useEffect } from "react";
 


interface Book {
  id: string;
  title: string;
  slug: string;
  description: string;
  status: string;
  visibility: string;
  created_at: string;
}

export default function BookManagerPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newSlug, setNewSlug] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchBooks();
  }, []);

  const fetchBooks = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("http:
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Lỗi hệ thống");
      setBooks(data);
    } catch (err: any) {
      console.error(err);
      setError("Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBook = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        throw new Error("Không tìm thấy thông tin đăng nhập");
      }
      const res = await fetch("http:
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: newTitle,
          slug: newSlug,
          description: newDescription,
        }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Lỗi hệ thống");
      }
      setIsModalOpen(false);
      setNewTitle("");
      setNewSlug("");
      setNewDescription("");
      fetchBooks();
    } catch (err: any) {
      console.error(err);
      const detail = err.message || "Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.";
      setError(typeof detail === 'string' ? detail : "Đã xảy ra lỗi khi tạo tài liệu.");
    } finally {
      setCreating(false);
    }
  };

  const handleSlugify = (title: string) => {
    setNewTitle(title);
    if (!newSlug || newSlug.trim() === "") {
      const generatedSlug = title
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[đĐ]/g, "d")
        .replace(/([^0-9a-z-\s])/g, "")
        .replace(/(\s+)/g, "-")
        .replace(/-+/g, "-")
        .replace(/^-+|-+$/g, "");
      setNewSlug(generatedSlug);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between border-b pb-4 border-gray-200">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Quản lý tài liệu</h1>
          <p className="text-sm text-gray-500 mt-1">Quản lý toàn bộ danh sách tài liệu trên hệ thống</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-black hover:bg-gray-800 text-white px-4 py-2 text-sm font-medium transition-colors"
        >
          Thêm tài liệu mới
        </button>
      </div>

      {error && (
        <div className="p-4 border border-black bg-zinc-50 text-black text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <p className="text-sm text-gray-500">Đang tải dữ liệu</p>
        </div>
      ) : books.length === 0 ? (
        <div className="text-center p-12 border border-gray-200 border-dashed">
          <p className="text-sm text-gray-500">Chưa có tác phẩm nào trong hệ thống.</p>
        </div>
      ) : (
        <div className="border border-gray-200 bg-white">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 border-b border-gray-200 text-gray-700">
              <tr>
                <th className="px-4 py-3 font-medium">Tên tài liệu</th>
                <th className="px-4 py-3 font-medium">Đường dẫn (Slug)</th>
                <th className="px-4 py-3 font-medium">Trạng thái</th>
                <th className="px-4 py-3 font-medium">Quyền xem</th>
                <th className="px-4 py-3 font-medium whitespace-nowrap w-24">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {books.map((book) => (
                <tr key={book.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{book.title}</td>
                  <td className="px-4 py-3 text-gray-500">{book.slug}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 border border-gray-200 text-xs font-medium text-gray-600 bg-gray-50">
                      {book.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{book.visibility}</td>
                  <td className="px-4 py-3 text-right">
                    <button className="text-gray-600 hover:text-black font-medium transition-colors">Sửa</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white border border-gray-200 w-full max-w-lg ">
            <form onSubmit={handleCreateBook}>
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-lg font-semibold tracking-tight">Thêm tài liệu mới</h2>
                <p className="text-sm text-gray-500 mt-1">Nhập thông tin cơ bản cho tác phẩm mới.</p>
              </div>
              
              <div className="p-6 space-y-4">
                <div className="space-y-1.5">
                  <label htmlFor="title" className="text-sm font-medium text-gray-900">
                    Tên tài liệu
                  </label>
                  <input
                    id="title"
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => handleSlugify(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 focus:outline-none focus:border-black focus:ring-1 focus:ring-black bg-white"
                    placeholder="Ví dụ: Lược sử thời gian"
                  />
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="slug" className="text-sm font-medium text-gray-900">
                    Đường dẫn tĩnh (Slug)
                  </label>
                  <input
                    id="slug"
                    type="text"
                    required
                    value={newSlug}
                    onChange={(e) => setNewSlug(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 focus:outline-none focus:border-black focus:ring-1 focus:ring-black bg-gray-50 text-gray-700"
                    placeholder="vi-du-luoc-su-thoi-gian"
                  />
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="description" className="text-sm font-medium text-gray-900">
                    Mô tả ngắn
                  </label>
                  <textarea
                    id="description"
                    rows={3}
                    value={newDescription}
                    onChange={(e) => setNewDescription(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 focus:outline-none focus:border-black focus:ring-1 focus:ring-black bg-white resize-none"
                    placeholder="Mô tả tóm tắt nội dung tài liệu"
                  />
                </div>
              </div>

              <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-black hover:bg-gray-100 border border-transparent transition-colors"
                  disabled={creating}
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-black hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  disabled={creating}
                >
                  {creating ? "Đang lưu" : "Xác nhận tạo"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}