import Link from "next/link";
import { ArrowRight, CheckCircle2, GitBranch, SearchCheck, Sparkles } from "lucide-react";

const capabilities = [
  {
    icon: SearchCheck,
    title: "Liên kết truy vết",
    description: "Liên kết yêu cầu, tiêu chí chấp nhận và ca kiểm thử theo đúng phiên bản nguồn",
  },
  {
    icon: GitBranch,
    title: "Phân tích thay đổi",
    description: "Phân tích ảnh hưởng và tạo đề xuất bảo trì mà không sửa âm thầm dữ liệu đã duyệt",
  },
  {
    icon: Sparkles,
    title: "Hỗ trợ bằng AI",
    description:
      "AI hỗ trợ tạo và rà soát bản nháp nhưng quyết định cuối cùng luôn thuộc về con người",
  },
];

const workflow = [
  "Chuẩn hóa và đặt phiên bản yêu cầu làm nguồn chính thức",
  "Thiết kế kịch bản và ca kiểm thử có liên kết truy vết",
  "Theo dõi độ phủ, lần chạy, lỗi và ảnh hưởng thay đổi",
];

export default function HomePage() {
  return (
    <main className="min-h-[100dvh] overflow-x-hidden bg-[#eef3ef] text-ink">
      <nav
        className="border-b border-brand/10 bg-white/80 backdrop-blur-md"
        aria-label="Điều hướng trang chủ"
      >
        <div className="mx-auto flex h-[72px] w-full max-w-[1200px] items-center justify-between px-5 md:px-8">
          <Link
            href="/"
            className="flex items-center gap-3 text-[19px] font-semibold tracking-[-0.035em]"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand text-[13px] font-bold text-white">
              Q
            </span>
            <span>QA Intelligence</span>
          </Link>
          <div className="flex items-center gap-2">
            <Link
              href="/dang-nhap"
              className="hidden rounded-control px-4 py-2 text-[14px] font-semibold text-ink-muted transition hover:bg-surface hover:text-ink sm:inline-flex"
            >
              Đăng nhập
            </Link>
            <Link href="/dang-ky" className="apple-button">
              Bắt đầu
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </nav>

      <section className="mx-auto grid w-full max-w-[1200px] gap-12 px-5 py-16 md:px-8 md:py-24 lg:grid-cols-[minmax(0,1.08fr)_minmax(420px,0.92fr)] lg:items-center">
        <div>
          <h1 className="max-w-3xl text-[44px] font-semibold leading-[1.02] tracking-[-0.055em] sm:text-[58px] lg:text-[66px]">
            Quản lý kiểm thử phần mềm
          </h1>
          <p className="mt-7 max-w-2xl text-[17px] leading-8 text-ink-muted md:text-[19px]">
            Quản lý yêu cầu phiên bản ca kiểm thử truy vết thay đổi lần chạy và lỗi trong cùng một
            hệ thống
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link href="/dang-ky" className="apple-button px-6">
              Tạo tài khoản
              <ArrowRight size={17} />
            </Link>
            <Link href="/dang-nhap" className="secondary-button px-6">
              Vào không gian kiểm thử
            </Link>
          </div>
        </div>

        <div className="relative">
          <div className="absolute -inset-8 rounded-full bg-brand/10 blur-3xl" />
          <div className="relative overflow-hidden rounded-3xl border border-brand/15 bg-[#193d34] p-6 text-white shadow-[0_30px_90px_rgba(26,61,52,0.22)] md:p-8">
            <div className="flex items-center justify-between border-b border-white/15 pb-5">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.17em] text-white/60">
                  Tổng quan dự án
                </p>
                <h2 className="mt-2 text-[22px] font-semibold">Dự án thanh toán</h2>
              </div>
              <span className="rounded-full bg-white/10 px-3 py-1 text-[12px] font-semibold">
                Đang hoạt động
              </span>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-3">
              {[
                ["96%", "Độ phủ yêu cầu"],
                ["84", "Ca kiểm thử"],
                ["7", "Thay đổi cần duyệt"],
                ["3", "Lỗi đang mở"],
              ].map(([value, label]) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
                  <p className="text-[28px] font-semibold tracking-[-0.04em]">{value}</p>
                  <p className="mt-2 text-[12px] leading-5 text-white/65">{label}</p>
                </div>
              ))}
            </div>
            <div className="mt-6 rounded-2xl bg-white p-5 text-ink">
              <p className="text-[12px] font-bold uppercase tracking-[0.12em] text-brand">
                Quyết định chờ duyệt
              </p>
              <div className="mt-4 space-y-3">
                {["Xác nhận liên kết truy vết", "Áp dụng đề xuất bảo trì"].map((item) => (
                  <div key={item} className="flex items-center gap-3 text-[13px] font-semibold">
                    <CheckCircle2 className="text-brand" size={17} />
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-brand/10 bg-white/70">
        <div className="mx-auto w-full max-w-[1200px] px-5 py-16 md:px-8 md:py-20">
          <div className="max-w-2xl">
            <h2 className="text-[32px] font-semibold leading-tight tracking-[-0.04em] md:text-[42px]">
              Chức năng
            </h2>
          </div>
          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {capabilities.map((item) => (
              <article
                key={item.title}
                className="rounded-2xl border border-border bg-surface p-6 shadow-[0_10px_30px_rgba(48,47,42,0.04)]"
              >
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-soft text-brand">
                  <item.icon size={21} />
                </span>
                <h3 className="mt-5 text-[18px] font-semibold">{item.title}</h3>
                <p className="mt-3 text-[14px] leading-7 text-ink-muted">{item.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid w-full max-w-[1200px] gap-10 px-5 py-16 md:px-8 md:py-20 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
        <div>
          <h2 className="text-[32px] font-semibold leading-tight tracking-[-0.04em]">Quy trình</h2>
        </div>
        <ol className="space-y-3">
          {workflow.map((item, index) => (
            <li
              key={item}
              className="grid grid-cols-[44px_1fr] items-center gap-4 rounded-2xl border border-border bg-white/70 p-4 md:p-5"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand text-[13px] font-bold text-white">
                {String(index + 1).padStart(2, "0")}
              </span>
              <p className="text-[14px] font-semibold leading-6 md:text-[15px]">{item}</p>
            </li>
          ))}
        </ol>
      </section>

      <footer className="border-t border-brand/10 bg-white/60">
        <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-3 px-5 py-8 text-[13px] text-ink-muted sm:flex-row sm:items-center sm:justify-between md:px-8">
          <span className="font-semibold text-ink">QA Intelligence</span>
          <div className="flex gap-5">
            <Link href="/dieu-khoan" className="hover:text-ink">
              Điều khoản
            </Link>
            <Link href="/dang-nhap" className="hover:text-ink">
              Đăng nhập
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
