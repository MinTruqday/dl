"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/features/authentication/services/session.service";
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
      showToast("Xác nhận điều khoản để tiếp tục", "info");
      return;
    }
    setLoading(true);

    try {
      await register(email, password, displayName, slug, agreedToTerms);
      showToast("Đã tạo tài khoản", "success");
      router.push("/dang-nhap");
    } catch (err: any) {
      showToast(
        err.message || "Không thể tạo tài khoản",
        "error",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white font-sans flex flex-col">
      <main className="flex-1 flex flex-col justify-center items-center px-4 sm:px-6 py-12">
        <div className="w-full max-w-[460px]">
          <div className="auth-panel">
            <div className="text-center mb-8">
              <h1 className="text-[28px] font-semibold text-ink tracking-tight">
                Đăng ký
              </h1>
            </div>

            <form className="space-y-5" onSubmit={handleRegister}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label
                    htmlFor="full_name"
                    className="block text-[13px] font-medium text-ink-muted mb-2 ml-1"
                  >
                    Tên hiển thị
                  </label>
                  <div className="relative">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink-muted" />
                    <input
                      id="full_name"
                      name="full_name"
                      type="text"
                      required
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="apple-input w-full pl-11"
                      placeholder=""
                    />
                  </div>
                </div>

                <div>
                  <label
                    htmlFor="slug"
                    className="block text-[13px] font-medium text-ink-muted mb-2 ml-1"
                  >
                    Tên tài khoản
                  </label>
                  <div className="relative">
                    <AtSign className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink-muted" />
                    <input
                      id="slug"
                      name="slug"
                      type="text"
                      required
                      value={slug}
                      onChange={(e) => setSlug(e.target.value)}
                      className="apple-input w-full pl-11"
                      placeholder=""
                    />
                  </div>
                </div>
              </div>

              <div>
                <label
                  htmlFor="email"
                  className="block text-[13px] font-medium text-ink-muted mb-2 ml-1"
                >
                  Địa chỉ email
                </label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink-muted" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="apple-input w-full pl-11"
                    placeholder=""
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-[13px] font-medium text-ink-muted mb-2 ml-1"
                >
                  Mật khẩu
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ink-muted" />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="apple-input w-full pl-11 pr-12"
                    placeholder=""
                  />
                  <button
                    type="button"
                    aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-ink-muted"
                  >
                    {showPassword ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
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
                    className="h-4 w-4 accent-[hsl(var(--brand))] rounded cursor-pointer"
                  />
                </div>
                <div className="ml-3">
                  <label htmlFor="terms" className="text-[13px] text-ink">
                    Tôi xác nhận đã đọc và đồng ý với{" "}
                    <button
                      type="button"
                      onClick={() => setShowTermsModal(true)}
                      className="font-medium text-brand hover:text-brand-hover"
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
                  className="pill-button w-full flex justify-center items-center gap-2 disabled:opacity-50"
                >
                  {loading && <Loader2 className="w-5 h-5 animate-spin" />}
                  {loading ? "Đang xử lý" : "Đăng ký tài khoản"}
                </button>
              </div>
            </form>

            <div className="mt-8 text-center border-t border-border pt-6">
              <p className="text-[15px] text-ink-muted">
                Đã có tài khoản{" "}
                <a
                  href="/dang-nhap"
                  className="font-medium text-brand hover:text-brand-hover"
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
        className="max-w-2xl"
      >
        <ModalHeader>
          <ModalTitle>
            Điều khoản và quy định
          </ModalTitle>
        </ModalHeader>
        <ModalContent className="max-h-[60vh] overflow-y-auto text-[15px] text-ink-muted">
          <section>
            <h4 className="font-semibold text-ink mb-2 text-[17px]">
              1. Quyền và trách nhiệm
            </h4>
            <p>
              Người dùng cam kết cung cấp thông tin chính xác. DocLib có quyền
              tạm khóa tài khoản nếu phát hiện hành vi gian lận hoặc vi phạm
              tiêu chuẩn cộng đồng.
            </p>
          </section>
          <section>
            <h4 className="font-semibold text-ink mb-2 text-[17px]">
              2. Bản quyền nội dung
            </h4>
            <p>
              Mọi tài liệu đăng tải phải thuộc quyền sở hữu của tác giả hoặc có
              sự cho phép hợp pháp. Chúng tôi nghiêm cấm hành vi đạo văn và sao
              chép trái phép.
            </p>
          </section>
          <section>
            <h4 className="font-semibold text-ink mb-2 text-[17px]">
              3. Giao dịch tài chính
            </h4>
            <p>
              Các giao dịch mua sách và nạp tiền là không hoàn trả. Người dùng
              cần kiểm tra kỹ thông tin trước khi thực hiện thanh toán.
            </p>
          </section>
          <section>
            <h4 className="font-semibold text-ink mb-2 text-[17px]">
              4. Bảo mật dữ liệu
            </h4>
            <p>
              DocLib cam kết bảo mật thông tin cá nhân và không chia sẻ cho bên
              thứ ba khi chưa có sự đồng ý của người dùng, trừ trường hợp yêu
              cầu từ pháp luật.
            </p>
          </section>
        </ModalContent>
        <ModalFooter>
          <button
            onClick={() => {
              setAgreedToTerms(true);
              setShowTermsModal(false);
            }}
            className="pill-button"
          >
            Đồng ý
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
