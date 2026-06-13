"use client";

import { ChangeEvent, FormEvent, useState, useEffect } from "react";
import Navigation from "@/shared/components/common/Navigation";
import { resetPasswordAPI } from "@/features/auth/services/authentication.service";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/shared/contexts/Toast";
import { Loader2 } from "lucide-react";

export default function ResetPasswordPage() {
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  useEffect(() => {
    if (!token) {
      router.replace("/forgot-password");
    }
  }, [token, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!newPassword || newPassword.length < 6) {
      showToast("Mật khẩu mới tối thiểu 6 ký tự", "error");
      return;
    }

    try {
      setLoading(true);
      const data = await resetPasswordAPI(token, newPassword);
      showToast(data.message || "Đã đặt lại mật khẩu thành công", "success");
      setTimeout(() => router.push("/login"), 1500);
    } catch (err: any) {
      showToast(err.message || "Đặt lại mật khẩu thất bại", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white font-sans">
      <Navigation />

      <div className="w-full max-w-[1280px] mx-auto px-6 py-6 min-h-[calc(100dvh-80px)] flex flex-col justify-center items-center mt-16">
        <div className="w-full max-w-md w-full animate-in fade-in slide-in-from-bottom-8 duration-300">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold tracking-tight text-black">
              Mật khẩu mới
            </h2>
            <p className="mt-2 text-sm text-zinc-500">
              Thiết lập mật khẩu mới cho tài khoản của bạn
            </p>
          </div>

          <div className="w-full">
            <div className="bg-white py-10 px-6 sm:px-12 border border-zinc-200 rounded-2xl">
              <form className="space-y-6" onSubmit={handleSubmit}>
                <div>
                  <label
                    htmlFor="new-password"
                    className="block text-sm font-medium text-black"
                  >
                    Mật khẩu mới
                  </label>
                  <div className="mt-2">
                    <input
                      id="new-password"
                      name="new-password"
                      type="password"
                      required
                      value={newPassword}
                      onChange={(e: ChangeEvent<HTMLInputElement>) =>
                        setNewPassword(e.target.value)
                      }
                      className="appearance-none block w-full px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-2xl focus:outline-none focus:ring-0 focus:border-zinc-200 text-sm text-black"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-3 h-12 text-sm font-medium text-white bg-black disabled:bg-zinc-200 disabled:text-zinc-500 rounded-2xl"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {loading ? "Đang xử lý" : "Cập nhật mật khẩu"}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
