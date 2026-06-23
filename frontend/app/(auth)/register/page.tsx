"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/features/auth/services/user_authentication.service";
import { Loader2, Eye, EyeOff, User, AtSign, Mail, Lock } from "lucide-react";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";

export default function RegisterPage() {
  const [displayName, setDisplayName] = useState("");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const { showToast } = useToast();
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agreedToTerms) {
      showToast("Bạn cần đồng ý với điều khoản để tiếp tục", "info");
      return;
    }
    setLoading(true);

    try {
      await register(email, password, displayName, slug, agreedToTerms);
      showToast(
        "Đăng ký thành công",
        "success",
      );
      router.push("/login");
    } catch (err: any) {
      showToast(
        err.message || "Tên đăng nhập hoặc email đã được sử dụng",
        "error",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 font-sans selection:bg-zinc-900 selection:text-white flex flex-col">
      <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-12">
        <div className="w-full max-w-[460px]">
          <div className="auth-panel">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold tracking-tight text-black">
                Đăng ký
              </h1>
              <p className="mt-2 text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                Tham gia hệ thống thư viện thông minh DocLib
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleRegister}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label
                    htmlFor="full_name"
                    className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 ml-1"
                  >
                    Tên hiển thị
                  </label>
                  <div className="relative">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                    <input
                      id="full_name"
                      name="full_name"
                      type="text"
                      required
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="w-full bg-white border border-zinc-200 rounded-3xl pl-11 pr-4 py-3 text-sm font-medium focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm transition-all duration-200"
                      placeholder="Nguyễn Văn A"
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="slug"
                    className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 ml-1"
                  >
                    Tên tài khoản
                  </label>
                  <div className="relative">
                    <AtSign className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                    <input
                      id="slug"
                      name="slug"
                      type="text"
                      required
                      value={slug}
                      onChange={(e) => setSlug(e.target.value)}
                      className="w-full bg-white border border-zinc-200 rounded-3xl pl-11 pr-4 py-3 text-sm font-medium focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm transition-all duration-200"
                      placeholder="nguyenvana"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label
                  htmlFor="email"
                  className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 ml-1"
                >
                  Địa chỉ email
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-white border border-zinc-200 rounded-3xl pl-11 pr-4 py-3 text-sm font-medium focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm transition-all duration-200"
                    placeholder="nguyenvana@example.com"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2 ml-1"
                >
                  Mật khẩu
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-white border border-zinc-200 rounded-3xl pl-11 pr-12 py-3 text-sm font-medium focus:bg-white focus:border-black focus:outline-none placeholder:text-zinc-300 shadow-sm transition-all duration-200"
                    placeholder="Tối thiểu 6 ký tự"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-black transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-start pt-2 ml-1">
                <div className="flex items-center h-5">
                  <input
                    id="terms"
                    name="terms"
                    type="checkbox"
                    checked={agreedToTerms}
                    onChange={(e) => setAgreedToTerms(e.target.checked)}
                    required
                    className="h-4 w-4 border border-zinc-300 rounded text-black focus:ring-0 cursor-pointer transition-colors"
                  />
                </div>
                <div className="ml-3 text-xs">
                  <label htmlFor="terms" className="text-zinc-500 font-medium leading-relaxed">
                    Tôi xác nhận đã đọc và đồng ý với{" "}
                    <button
                      type="button"
                      onClick={() => setShowTermsModal(true)}
                      className="text-black font-bold hover:text-zinc-600 transition-colors"
                    >
                      Điều khoản & Quy định
                    </button>
                  </label>
                </div>
              </div>

              <div className="pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center gap-2 h-12 text-xs font-bold text-white bg-black rounded-3xl transition-all duration-200 hover:scale-[1.02] shadow-md disabled:bg-zinc-200 disabled:text-zinc-500 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {loading ? "Đang xử lý" : "Đăng ký tài khoản"}
                </button>
              </div>
            </form>

            <div className="mt-8 text-center border-t border-zinc-100 pt-6">
              <p className="text-xs font-medium text-zinc-500">
                Đã có tài khoản?{" "}
                <a
                  href="/login"
                  className="font-bold text-black transition-colors hover:text-zinc-600"
                >
                  Đăng nhập
                </a>
              </p>
            </div>
          </div>
        </div>
      </main>

      <Modal
        isOpen={showTermsModal}
        onClose={() => setShowTermsModal(false)}
        className="max-w-2xl bg-white/95 backdrop-blur-md rounded-3xl border border-zinc-100 shadow-2xl"
      >
        <ModalHeader className="border-b border-zinc-100 px-8 py-6">
          <ModalTitle className="text-sm font-bold text-black tracking-tight uppercase">Điều khoản và quy định</ModalTitle>
        </ModalHeader>
        <ModalContent className="max-h-[60vh] overflow-y-auto px-8 py-6 text-xs text-zinc-500 font-medium leading-relaxed space-y-6">
          <section>
            <h4 className="font-bold text-zinc-900 mb-2 uppercase tracking-widest text-[10px]">
              1. Quyền và trách nhiệm
            </h4>
            <p>
              Người dùng cam kết cung cấp thông tin chính xác. DocLib có quyền
              tạm khóa tài khoản nếu phát hiện hành vi gian lận hoặc vi phạm
              tiêu chuẩn cộng đồng.
            </p>
          </section>
          <section>
            <h4 className="font-bold text-zinc-900 mb-2 uppercase tracking-widest text-[10px]">
              2. Bản quyền nội dung
            </h4>
            <p>
              Mọi tài liệu đăng tải phải thuộc quyền sở hữu của tác giả hoặc có
              sự cho phép hợp pháp. Chúng tôi nghiêm cấm hành vi đạo văn và sao
              chép trái phép.
            </p>
          </section>
          <section>
            <h4 className="font-bold text-zinc-900 mb-2 uppercase tracking-widest text-[10px]">
              3. Giao dịch tài chính
            </h4>
            <p>
              Các giao dịch mua sách và nạp tiền là không hoàn trả. Người dùng
              cần kiểm tra kỹ thông tin trước khi thực hiện thanh toán.
            </p>
          </section>
          <section>
            <h4 className="font-bold text-zinc-900 mb-2 uppercase tracking-widest text-[10px]">
              4. Bảo mật dữ liệu
            </h4>
            <p>
              DocLib cam kết bảo mật thông tin cá nhân và không chia sẻ cho bên
              thứ ba khi chưa có sự đồng ý của người dùng, trừ trường hợp yêu
              cầu từ pháp luật.
            </p>
          </section>
        </ModalContent>
        <ModalFooter className="border-t border-zinc-100 px-8 py-6 flex justify-end bg-zinc-50/50 rounded-b-3xl">
          <button
            onClick={() => {
              setAgreedToTerms(true);
              setShowTermsModal(false);
            }}
            className="w-full sm:w-auto px-8 h-11 bg-black text-white text-xs font-bold rounded-2xl transition-all duration-200 hover:scale-105 shadow-md"
          >
            Đồng ý
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
