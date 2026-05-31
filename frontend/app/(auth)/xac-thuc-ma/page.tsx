"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import Navigation from "@/components/Navigation";
import { verifyCodeAPI } from "@/services/authentication.service";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/contexts/Toast";
import { Loader2 } from "lucide-react";

export default function VerifyCodePage() {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";

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
        router.push(
          `/dat-lai-mat-khau?token=${encodeURIComponent(token.trim())}`,
        );
      }, 1200);
    } catch (err: any) {
      showToast(err.message || "Mã xác thực không hợp lệ", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white font-sans">
      <Navigation />

      <div className="w-full max-w-[1280px] mx-auto px-6 py-6 min-h-[calc(100dvh-80px)] flex flex-col justify-center items-center mt-16">
        <div className="w-full max-w-md w-full">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-black">
          Xác thực mã
        </h2>
        <p className="mt-2 text-sm text-zinc-500">
          Mã xác thực đã được gửi tới {email}
        </p>
      </div>

      <div className="w-full">
        <div className="bg-white py-10 px-6 sm:px-12 border border-zinc-200 rounded-2xl">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="token"
                className="block text-sm font-medium text-black"
              >
                Mã xác thực
              </label>
              <div className="mt-2">
                <input
                  id="token"
                  name="token"
                  type="text"
                  required
                  value={token}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setToken(e.target.value)
                  }
                  className="appearance-none block w-full px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-2xl focus:outline-none focus:ring-0 focus:border-zinc-200 text-center text-2xl tracking-[0.25em] font-medium text-black uppercase"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-3 h-12 text-sm font-medium text-white bg-black disabled:bg-zinc-200 disabled:text-zinc-500 rounded-2xl"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? "Đang xử lý" : "Tiếp tục"}
            </button>
          </form>

          <div className="mt-8 text-sm text-center">
            <button
              onClick={() => router.back()}
              className="text-zinc-500 font-medium underline"
            >
              Quay lại
            </button>
          </div>
        </div>
      </div>
    </div>
    </div>
    </div>
  );
}
