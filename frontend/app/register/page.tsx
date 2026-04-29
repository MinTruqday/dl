"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/app/lib/api";
import Navbar from "@/app/components/Navbar";
import { X, Loader2 } from "lucide-react";
import { useToast } from "@/app/contexts/ToastContext";
import PasskeyPrompt from "@/app/components/PasskeyPrompt";

export default function RegisterPage() {
  const [displayName, setDisplayName] = useState("");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const { showToast } = useToast();
  const router = useRouter();

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agreedToTerms) {
      showToast("Bạn cần đồng ý với điều khoản để tiếp tục", "info");
      return;
    }
    setLoading(true);

    try {
      await register(email, password, displayName, slug, agreedToTerms);
      setRegisteredEmail(email);
      showToast("Đăng ký thành công. Bạn có muốn thiết lập Passkey không?", "success");
    } catch (err: any) {
      showToast(err.message || "Tên đăng nhập hoặc email đã được sử dụng", "error");
    } finally {
      setLoading(false);
    }
  };

  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans animate-in fade-in duration-300">
      <Navbar />

      {registeredEmail && (
        <PasskeyPrompt 
          email={registeredEmail} 
          onClose={() => router.push("/login")} 
          onSuccess={() => router.push("/login")} 
        />
      )}
      <div
        className="sm:mx-auto sm:w-full sm:max-w-md mt-16 transition-all duration-300 animate-in slide-in-from-bottom-4"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <h2 className="text-center text-4xl font-bold tracking-tight text-black">
          Đăng ký DocLib
        </h2>
        <p className="mt-3 text-center text-base text-zinc-500">
          Đã có tài khoản?{" "}
          <a href="/login" className="font-bold text-black hover:underline active:scale-95 inline-block transition-transform">
            Đăng nhập ngay
          </a>
        </p>
      </div>

      <div
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-md transition-all duration-300 delay-150 animate-in slide-in-from-bottom-4"
        style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(16px)" }}
      >
        <div className="bg-white py-8 px-4 sm:px-10 border border-zinc-200 rounded-sm">
          <form className="space-y-5" onSubmit={handleRegister}>
            <div>
              <label htmlFor="display_name" className="block text-base font-bold text-black">
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
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-sm focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-base transition-all"
                />
              </div>
            </div>

            <div>
              <label htmlFor="slug" className="block text-base font-bold text-black">
                Tên tài khoản
              </label>
              <div className="mt-1 flex">
                <span className="inline-flex items-center px-3 border border-r-0 border-zinc-200 bg-zinc-50 text-zinc-400 sm:text-sm rounded-l-sm">
                  @
                </span>
                <input
                  id="slug"
                  name="slug"
                  type="text"
                  required
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="flex-1 min-w-0 block w-full px-4 py-3 border border-zinc-200 rounded-r-sm focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-base transition-all"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-base font-bold text-black">
                Địa chỉ email
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
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-sm focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-base transition-all"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-base font-bold text-black">
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
                  className="appearance-none block w-full px-4 py-3 border border-zinc-200 rounded-sm focus:outline-none focus:ring-1 focus:ring-black focus:border-black text-base transition-all"
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
                className="h-4 w-4 text-black focus:ring-black border-zinc-300 rounded-sm"
              />
              <label htmlFor="terms" className="ml-2 block text-base text-zinc-600">
                Tôi đồng ý với các{" "}
                <button
                  type="button"
                  onClick={() => setShowTermsModal(true)}
                  className="text-black underline font-bold active:scale-95 transition-transform"
                >
                  Điều khoản và quy định
                </button>{" "}
                của nền tảng
              </label>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center gap-3 py-3 px-4 text-base font-bold text-white bg-black hover:bg-zinc-800 transition-all rounded-sm disabled:bg-zinc-400 disabled:cursor-not-allowed active:scale-95"
              >
                {loading && <Loader2 className="w-5 h-5 animate-spin" />}
                {loading ? "Đang xử lý" : "Đăng ký ngay"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {showTermsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 animate-in fade-in duration-300">
          <div className="w-full max-w-2xl bg-white border border-zinc-200 p-8 rounded-sm animate-in zoom-in-95 duration-300">
            <div className="flex justify-between items-center mb-6 border-b border-zinc-100 pb-4">
              <h3 className="text-xl font-bold tracking-tighter">Điều khoản và quy định DocLib</h3>
              <button
                onClick={() => setShowTermsModal(false)}
                className="text-zinc-400 hover:text-black p-1 transition-colors active:scale-90"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="max-h-[60vh] overflow-y-auto pr-4 text-sm text-zinc-500 leading-relaxed space-y-6">
              <section>
                <h4 className="font-bold text-black mb-2 text-[12px]">1. Quyền và trách nhiệm</h4>
                <p>
                  Người dùng cam kết cung cấp thông tin chính xác. DocLib có quyền tạm khóa tài khoản nếu phát hiện
                  hành vi gian lận hoặc vi phạm tiêu chuẩn cộng đồng.
                </p>
              </section>
              <section>
                <h4 className="font-bold text-black mb-2 text-[12px]">2. Bản quyền nội dung</h4>
                <p>
                  Mọi tài liệu đăng tải phải thuộc quyền sở hữu của tác giả hoặc có sự cho phép hợp pháp. Chúng tôi
                  nghiêm cấm hành vi đạo văn và sao chép trái phép.
                </p>
              </section>
              <section>
                <h4 className="font-bold text-black mb-2 text-[12px]">3. Giao dịch tài chính</h4>
                <p>
                  Các giao dịch mua sách và nạp tiền là không hoàn trả. Người dùng cần kiểm tra kỹ thông tin trước khi
                  thực hiện thanh toán.
                </p>
              </section>
              <section>
                <h4 className="font-bold text-black mb-2 text-[12px]">4. Bảo mật dữ liệu</h4>
                <p>
                  DocLib cam kết bảo mật thông tin cá nhân và không chia sẻ cho bên thứ ba khi chưa có sự đồng ý của
                  người dùng, trừ trường hợp yêu cầu từ pháp luật.
                </p>
              </section>
            </div>
            <div className="mt-8 flex justify-end">
              <button
                onClick={() => {
                  setAgreedToTerms(true);
                  setShowTermsModal(false);
                }}
                className="px-8 py-3 bg-black text-white text-[12px] font-bold hover:bg-zinc-800 transition-all active:scale-95 rounded-sm"
              >
                Tôi đã hiểu và đồng ý
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}