"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import Navbar from "@/app/components/Navbar";
import { resetPasswordAPI } from "@/app/lib/api";
import { useRouter } from "next/navigation";

export default function ResetPasswordPage() {
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [info, setInfo] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setInfo("");

    if (!token.trim()) {
      setError("Vui lòng nhập mã khôi phục.");
      return;
    }
    if (!newPassword || newPassword.length < 6) {
      setError("Mật khẩu mới tối thiểu 6 ký tự.");
      return;
    }

    try {
      setLoading(true);
      const data = await resetPasswordAPI(token.trim(), newPassword);
      setInfo(data.message || "Đã đặt lại mật khẩu thành công.");
      setTimeout(() => router.push("/login"), 1200);
    } catch (err: any) {
      setError(err.message || "Đặt lại mật khẩu thất bại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <Navbar />
      <div className="sm:mx-auto sm:w-full sm:max-w-md mt-16">
        <h2 className="text-center text-3xl font-extrabold text-foreground font-bold">Đặt lại mật khẩu</h2>
        <p className="mt-2 text-center text-sm text-muted-foreground">Nhập mã khôi phục và mật khẩu mới.</p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-card py-8 px-4 shadow sm: sm:px-10 border border-border">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {info && <div className="bg-gray-100 border-l-4 border-black p-4  text-sm text-black">{info}</div>}
            {error && <div className="bg-gray-100 border-l-4 border-black p-4  text-sm text-black font-bold outline-black">{error}</div>}

            <div>
              <label htmlFor="token" className="block text-sm font-medium text-gray-700">Mã khôi phục</label>
              <div className="mt-1">
                <input
                  id="token"
                  name="token"
                  type="text"
                  required
                  value={token}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setToken(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-border   focus:outline-none focus:ring-black focus:border-black sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="new-password" className="block text-sm font-medium text-gray-700">Mật khẩu mới</label>
              <div className="mt-1">
                <input
                  id="new-password"
                  name="new-password"
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-border   focus:outline-none focus:ring-black focus:border-black sm:text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4  text-sm font-medium text-white bg-black hover:bg-zinc-800 disabled:opacity-50 tracking-widest"
            >
              {loading ? "ĐANG XỬ LÝ" : "ĐẶT LẠI MẬT KHẨU"}
            </button>
          </form>

          <div className="mt-4 text-sm text-center">
            <a href="/login" className="text-black hover:underline font-medium">Quay lại đăng nhập</a>
          </div>
        </div>
      </div>
    </div>
  );
}
