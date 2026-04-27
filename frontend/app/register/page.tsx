"use client";
import Navbar from "@/app/components/Navbar";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/app/lib/api";
import Link from "next/link";
import { X } from "lucide-react";
import { Notification } from "@/app/components/NotificationToast";

export default function RegisterPage() {
  const [displayName, setDisplayName] = useState("");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const [showTermsModal, setShowTermsModal] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agreedToTerms) {
      setError("Bạn cần đồng ý với điều khoản để tiếp tục.");
      return;
    }
    setLoading(true);
    setError("");

    try {
      await register(email, password, displayName, slug, agreedToTerms);
      router.push("/login");
    } catch (err: any) {
      setError(err.message || "Tên đăng nhập hoặc email đã được sử dụng.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <Navbar />
      <div className="sm:mx-auto sm:w-full sm:max-w-md mt-16">
        <h2 className="text-center text-3xl font-extrabold text-foreground font-bold">
          Đăng ký tài khoản DocLib
        </h2>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          Đã có tài khoản?{" "}
          <a href="/login" className="font-medium text-black hover:underline">
            Đăng nhập tài khoản DocLib
          </a>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-card py-8 px-4  sm: sm:px-10 border border-border">
          <form className="space-y-5" onSubmit={handleRegister}>
            {error && <Notification type="error" message={error} />}
            <div>
              <label htmlFor="display_name" className="block text-sm font-medium text-gray-700">
                Tên hiển thị
              </label>
              <div className="mt-1">
                <input
                  id="display_name"
                  name="display_name"
                  type="text"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-border   focus:outline-none focus:ring-black focus:border-black sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="slug" className="block text-sm font-medium text-gray-700">
                Tên tài khoản
              </label>
              <div className="mt-1 flex  ">
                <span className="inline-flex items-center px-3 rounded-l-md border border-r-0 border-border bg-background text-muted-foreground sm:text-sm">
                  @
                </span>
                <input
                  id="slug"
                  name="slug"
                  type="text"
                  required
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="flex-1 min-w-0 block w-full px-3 py-2  rounded-r-md border border-border focus:outline-none focus:ring-black focus:border-black sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Địa chỉ Email
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-border   focus:outline-none focus:ring-black focus:border-black sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Mật khẩu
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-border   focus:outline-none focus:ring-black focus:border-black sm:text-sm"
                />
              </div>
            </div>

            <div className="flex items-center">
              <input
                id="terms"
                name="terms"
                type="checkbox"
                checked={agreedToTerms}
                onChange={(e) => setAgreedToTerms(e.target.checked)}
                required
                className="h-4 w-4 text-black focus:ring-black border-border rounded"
              />
              <label htmlFor="terms" className="ml-2 block text-sm text-foreground">
                Tôi đồng ý với các <button type="button" onClick={() => setShowTermsModal(true)} className="text-black underline font-semibold">Điều khoản và Quy định</button> của nền tảng
              </label>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent   text-sm font-medium text-white bg-black hover:bg-gray-800 transition-colors disabled:bg-zinc-400 disabled:cursor-not-allowed"
              >
                {loading ? "Đang xử lý" : "Đăng ký"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {showTermsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl bg-white border border-black p-8 animate-in zoom-in duration-200">
            <div className="flex justify-between items-center mb-6 border-b border-black pb-4">
              <h3 className="text-xl font-bold tracking-tighter">Điều khoản & Quy định DocLib</h3>
              <button onClick={() => setShowTermsModal(false)} className="text-zinc-400 hover:text-black">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="max-h-[60vh] overflow-y-auto pr-4 text-sm text-zinc-600 leading-relaxed space-y-6 scrollbar-thin scrollbar-thumb-black">
              <section>
                <h4 className="font-bold text-black mb-2 text-[12px]">1. Quyền và Trách nhiệm</h4>
                <p>Người dùng cam kết cung cấp thông tin chính xác. DocLib có quyền tạm khóa tài khoản nếu phát hiện hành vi gian lận hoặc vi phạm tiêu chuẩn cộng đồng.</p>
              </section>
              <section>
                <h4 className="font-bold text-black mb-2 text-[12px]">2. Bản quyền Nội dung</h4>
                <p>Mọi tài liệu đăng tải phải thuộc quyền sở hữu của tác giả hoặc có sự cho phép hợp pháp. Chúng tôi nghiêm cấm hành vi đạo văn và sao chép trái phép.</p>
              </section>
              <section>
                <h4 className="font-bold text-black mb-2 text-[12px]">3. Giao dịch Tài chính</h4>
                <p>Các giao dịch mua sách và nạp tiền là không hoàn trả. Người dùng cần kiểm tra kỹ thông tin trước khi thực hiện thanh toán.</p>
              </section>
              <section>
                <h4 className="font-bold text-black mb-2 text-[12px]">4. Bảo mật Dữ liệu</h4>
                <p>DocLib cam kết bảo mật thông tin cá nhân và không chia sẻ cho bên thứ ba khi chưa có sự đồng ý của người dùng, trừ trường hợp yêu cầu từ pháp luật.</p>
              </section>
            </div>
            <div className="mt-8 flex justify-end gap-4">
              <button 
                onClick={() => { setAgreedToTerms(true); setShowTermsModal(false); }}
                className="px-6 py-2 bg-black text-white text-xs font-bold tracking-widest hover:bg-zinc-800 transition-all"
              >
                Tôi đã hiểu và Đồng ý
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}