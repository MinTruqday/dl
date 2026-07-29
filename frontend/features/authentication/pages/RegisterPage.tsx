"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/features/authentication/services/session.service";
import { useToast } from "@/shared/contexts/ToastContext";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/shared/components/ui/Modal";
import PasswordInput from "@/features/authentication/components/PasswordInput";
import AuthLayout from "@/features/authentication/components/AuthLayout";
import Link from "next/link";

export default function RegisterPage() {
  const [displayName, setDisplayName] = useState("");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const { showToast } = useToast();
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agreedToTerms) {
      showToast("Yêu cầu xác nhận thỏa thuận dịch vụ trước khi tiếp tục", "info");
      return;
    }
    setLoading(true);

    try {
      await register(email, password, displayName, slug, agreedToTerms);
      showToast("Khởi tạo hồ sơ định danh hoàn tất", "success");
      router.push("/dang-nhap");
    } catch (err: any) {
      showToast(
        err.message || "Lỗi trùng lặp dữ liệu định danh trong hệ thống",
        "error",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <AuthLayout
        title="Tạo tài khoản"
        footer={
          <>
            Đã có tài khoản{" "}
            <Link href="/dang-nhap" className="font-semibold text-[var(--brand)]">
              Đăng nhập
            </Link>
          </>
        }
      >
        <form className="space-y-5" onSubmit={handleRegister}>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                <div>
                  <label
                    htmlFor="full_name"
                    className="block text-[13px] font-medium text-[var(--ink-muted)] mb-2 ml-1"
                  >
                    Tên hiển thị
                  </label>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    autoComplete="name"
                    required
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="field-control w-full"
                  />
                </div>

                <div>
                  <label
                    htmlFor="slug"
                    className="block text-[13px] font-medium text-[var(--ink-muted)] mb-2 ml-1"
                  >
                    Tên tài khoản
                  </label>
                  <input
                    id="slug"
                    name="slug"
                    type="text"
                    autoComplete="username"
                    required
                    value={slug}
                    onChange={(e) => setSlug(e.target.value)}
                    className="field-control w-full"
                  />
                </div>
          </div>

          <div>
                <label
                  htmlFor="email"
                  className="block text-[13px] font-medium text-[var(--ink-muted)] mb-2 ml-1"
                >
                  Địa chỉ email
                </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="field-control w-full"
            />
          </div>

          <div>
                <label
                  htmlFor="password"
                  className="block text-[13px] font-medium text-[var(--ink-muted)] mb-2 ml-1"
                >
                  Mật khẩu
                </label>
            <PasswordInput
              id="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="flex items-start pt-2">
            <div className="flex h-5 items-center">
                  <input
                    id="terms"
                    name="terms"
                    type="checkbox"
                    checked={agreedToTerms}
                    onChange={(e) => setAgreedToTerms(e.target.checked)}
                    required
                    className="h-4 w-4 accent-[var(--brand)] rounded cursor-pointer"
                  />
                </div>
            <div className="ml-3">
                  <label htmlFor="terms" className="text-[13px] text-[var(--ink)]">
                    Tôi xác nhận đã đọc và đồng ý với{" "}
                    <button
                      type="button"
                      onClick={() => setShowTermsModal(true)}
                      className="font-medium text-[var(--brand)] hover:text-[var(--brand-hover)]"
                    >
                      Điều khoản và quy định
                    </button>
                  </label>
                </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="pill-button w-full disabled:opacity-50"
          >
            {loading ? "Đang xử lý" : "Tạo tài khoản"}
          </button>
        </form>
      </AuthLayout>

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
        <ModalContent className="max-h-[60vh] overflow-y-auto text-[15px] text-[var(--ink-muted)]">
          <section>
            <h4 className="font-semibold text-[var(--ink)] mb-2 text-[17px]">
              1. Quyền và trách nhiệm
            </h4>
            <p>
              Người dùng cam kết cung cấp thông tin chính xác. DocLib có quyền
              tạm khóa tài khoản nếu phát hiện hành vi gian lận hoặc vi phạm
              tiêu chuẩn cộng đồng.
            </p>
          </section>
          <section>
            <h4 className="font-semibold text-[var(--ink)] mb-2 text-[17px]">
              2. Bản quyền nội dung
            </h4>
            <p>
              Mọi tài liệu đăng tải phải thuộc quyền sở hữu của tác giả hoặc có
              sự cho phép hợp pháp. Chúng tôi nghiêm cấm hành vi đạo văn và sao
              chép trái phép.
            </p>
          </section>
          <section>
            <h4 className="font-semibold text-[var(--ink)] mb-2 text-[17px]">
              3. Giao dịch tài chính
            </h4>
            <p>
              Các giao dịch mua sách và nạp tiền là không hoàn trả. Người dùng
              cần kiểm tra kỹ thông tin trước khi thực hiện thanh toán.
            </p>
          </section>
          <section>
            <h4 className="font-semibold text-[var(--ink)] mb-2 text-[17px]">
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
    </>
  );
}
