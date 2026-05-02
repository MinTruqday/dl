"use client";

import { ChangeEvent, FormEvent, useState, useEffect } from "react";
import Navigation from "@/components/Navigation";
import { verifyCodeAPI } from "@/services/auth.service";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/contexts/ToastContext";
import { Loader2 } from "lucide-react";

export default function VerifyCodePage() {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();
  const [visible, setVisible] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!token.trim()) {
      showToast("Vui lòng nhập mã xác thực", "error");
      return;
    }

    try {
      setLoading(true);
      await verifyCodeAPI(token.trim());
      showToast("Mã xác thực hợp lệ", "success");
      setTimeout(() => {
        router.push(`/reset-password?token=${encodeURIComponent(token.trim())}`);
      }, 1200);
    } catch (err: any) {
      showToast(err.message || "Mã xác thực không hợp lệ", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <Navigation />
      <div
        className="sm:mx-auto sm:w-full sm:max-w-md mt-16 transition-all duration-300 animate-in fade-in"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <h2 className="text-center text-4xl font-bold tracking-tight text-black">
          Xác thực mã
        </h2>
        <p className="mt-3 text-center text-base text-zinc-500">
          Mã xác thực đã được gửi tới {email}
        </p>
      </div>

      <div
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-md transition-all duration-300 delay-150 animate-in slide-in-from-bottom-4"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <div className="bg-white py-8 px-4 sm:px-10 border border-zinc-200 rounded-sm">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="token" className="block text-base font-bold text-black">
                Mã xác thực
              </label>
              <div className="mt-1">
                <input
                  id="token"
                  name="token"
                  type="text"
                  placeholder=""
                  required
                  value={token}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setToken(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-sm focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-center text-2xl tracking-widest font-bold transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-3 py-3 px-4 text-base font-bold text-white bg-black hover:bg-zinc-800 disabled:bg-zinc-400 transition-all active:scale-95 rounded-sm"
            >
              {loading && <Loader2 className="w-5 h-5 animate-spin" />}
              {loading ? "Đang xử lý" : "Tiếp tục"}
            </button>
          </form>

          <div className="mt-4 text-sm text-center">
            <button 
              onClick={() => router.back()}
              className="text-zinc-400 hover:text-black font-medium transition-colors"
            >
              Quay lại
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
