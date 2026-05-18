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
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <Navigation />
      <div className="sm:mx-auto sm:w-full sm:max-w-md mt-16">
        <h2 className="text-center text-3xl font-bold tracking-tight text-black">
          Xác thực mã
        </h2>
        <p className="mt-2 text-center text-sm text-zinc-500">
          Mã xác thực đã được gửi tới {email}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-10 px-6 sm:px-12 border border-zinc-200 rounded-none">
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
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-none focus:outline-none focus:ring-0 focus:border-black text-center text-2xl tracking-[0.25em] font-medium text-black uppercase"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-3 h-12 text-sm font-medium text-white bg-black disabled:bg-zinc-200 disabled:text-zinc-500 rounded-none"
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
  );
}
