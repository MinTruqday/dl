"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/services/authentication.service";
import Navigation from "@/components/Navigation";
import { Loader2 } from "lucide-react";
import { useToast } from "@/contexts/Toast";
import Passkey from "@/components/Passkey";
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalContent,
  ModalFooter,
} from "@/components/ui/Modal";

export default function RegisterPage() {
  const [displayName, setDisplayName] = useState("");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);
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
      setRegisteredEmail(email);
      showToast(
        "Đăng ký thành công. Bạn có muốn thiết lập Passkey không?",
        "success",
      );
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
    <div className="min-h-screen bg-white flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <Navigation />

      {registeredEmail && (
        <Passkey
          email={registeredEmail}
          onClose={() => router.push("/dang-nhap")}
          onSuccess={() => router.push("/dang-nhap")}
        />
      )}
      
      <div className="sm:mx-auto sm:w-full sm:max-w-md mt-16">
        <h2 className="text-center text-3xl font-bold tracking-tight text-black">
          Đăng ký
        </h2>
        <p className="mt-2 text-center text-sm text-zinc-500">
          Đã có tài khoản?{" "}
          <a
            href="/dang-nhap"
            className="font-medium text-black underline"
          >
            Đăng nhập ngay
          </a>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-10 px-6 sm:px-12 border border-zinc-200 rounded-none">
          <form className="space-y-6" onSubmit={handleRegister}>
            <div>
              <label
                htmlFor="full_name"
                className="block text-sm font-medium text-black"
              >
                Tên hiển thị
              </label>
              <div className="mt-2">
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-none focus:outline-none focus:ring-0 focus:border-zinc-200 text-sm text-black"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="slug"
                className="block text-sm font-medium text-black"
              >
                Tên tài khoản
              </label>
              <div className="mt-2 flex">
                <span className="inline-flex items-center px-4 border border-r-0 border-zinc-200 bg-zinc-50 text-zinc-500 text-sm rounded-none">
                  @
                </span>
                <input
                  id="slug"
                  name="slug"
                  type="text"
                  required
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="flex-1 min-w-0 block w-full px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-none focus:outline-none focus:ring-0 focus:border-zinc-200 text-sm text-black"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-black"
              >
                Địa chỉ email
              </label>
              <div className="mt-2">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-none focus:outline-none focus:ring-0 focus:border-zinc-200 text-sm text-black"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-black"
              >
                Mật khẩu
              </label>
              <div className="mt-2">
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 bg-zinc-50 border border-zinc-200 rounded-none focus:outline-none focus:ring-0 focus:border-zinc-200 text-sm text-black"
                />
              </div>
            </div>

            <div className="flex items-start mt-4">
              <div className="flex items-center h-5">
                <input
                  id="terms"
                  name="terms"
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                  required
                  className="h-4 w-4 border border-zinc-300 rounded-none text-black focus:ring-0 cursor-pointer"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="terms" className="text-zinc-600">
                  Tôi đồng ý với các{" "}
                  <button
                    type="button"
                    onClick={() => setShowTermsModal(true)}
                    className="text-black font-medium underline"
                  >
                    Điều khoản và quy định
                  </button>{" "}
                  của nền tảng
                </label>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center items-center gap-3 h-12 text-sm font-medium text-white bg-black rounded-none disabled:bg-zinc-200 disabled:text-zinc-500"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? "Đang xử lý" : "Đăng ký"}
              </button>
            </div>
          </form>
        </div>
      </div>

      <Modal
        isOpen={showTermsModal}
        onClose={() => setShowTermsModal(false)}
        className="max-w-2xl"
      >
        <ModalHeader>
          <ModalTitle>Điều khoản và quy định</ModalTitle>
        </ModalHeader>
        <ModalContent className="max-h-[60vh] overflow-y-auto p-6 text-sm text-zinc-600 leading-relaxed space-y-6">
          <section>
            <h4 className="font-medium text-black mb-2">
              1. Quyền và trách nhiệm
            </h4>
            <p>
              Người dùng cam kết cung cấp thông tin chính xác. DocLib có quyền
              tạm khóa tài khoản nếu phát hiện hành vi gian lận hoặc vi phạm
              tiêu chuẩn cộng đồng.
            </p>
          </section>
          <section>
            <h4 className="font-medium text-black mb-2">
              2. Bản quyền nội dung
            </h4>
            <p>
              Mọi tài liệu đăng tải phải thuộc quyền sở hữu của tác giả hoặc có
              sự cho phép hợp pháp. Chúng tôi nghiêm cấm hành vi đạo văn và sao
              chép trái phép.
            </p>
          </section>
          <section>
            <h4 className="font-medium text-black mb-2">
              3. Giao dịch tài chính
            </h4>
            <p>
              Các giao dịch mua sách và nạp tiền là không hoàn trả. Người dùng
              cần kiểm tra kỹ thông tin trước khi thực hiện thanh toán.
            </p>
          </section>
          <section>
            <h4 className="font-medium text-black mb-2">
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
            className="px-6 h-10 bg-black text-white text-sm font-medium rounded-none"
          >
            Tôi đã hiểu và đồng ý
          </button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
