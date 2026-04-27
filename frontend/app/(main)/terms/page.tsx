import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Điều khoản sử dụng | DocLib",
  description: "Điều khoản sử dụng và chính sách bảo mật của nền tảng DocLib.",
};

export default function TermsPage() {
  return (
    <div className="w-full max-w-[800px] mx-auto px-6 lg:px-8 py-12 md:py-20 bg-white min-h-screen animate-in fade-in duration-300">
      <div className="mb-16 border-b border-black pb-12">
        <span className="text-[13px] font-bold tracking-[0.3em] text-zinc-400 block mb-4">Pháp lý</span>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tighter text-black mb-6">
          Điều khoản sử dụng
        </h1>
        <p className="text-zinc-500 text-sm font-medium">Cập nhật lần cuối: Tháng 4, 2026</p>
      </div>

      <div className="space-y-12 text-sm text-zinc-700 leading-relaxed">
        <section>
          <h2 className="text-lg font-bold text-black mb-4 tracking-tight">1. Giới thiệu</h2>
          <p>
            DocLib là nền tảng lưu trữ, chia sẻ và nghiên cứu tài liệu số. Bằng việc truy cập và sử dụng dịch vụ, bạn đồng ý tuân thủ toàn bộ các điều khoản được nêu trong tài liệu này.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-bold text-black mb-4 tracking-tight">2. Tài khoản người dùng</h2>
          <p>
            Mỗi người dùng chịu trách nhiệm bảo mật thông tin tài khoản của mình. DocLib không chịu trách nhiệm cho bất kỳ thiệt hại nào phát sinh từ việc sử dụng trái phép tài khoản.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-bold text-black mb-4 tracking-tight">3. Quyền sở hữu trí tuệ</h2>
          <p>
            Tác giả giữ toàn quyền sở hữu trí tuệ đối với nội dung tài liệu đã xuất bản trên nền tảng. DocLib cam kết bảo vệ quyền lợi của tác giả thông qua hệ thống bảo vệ bản quyền và chính sách chống sao chép.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-bold text-black mb-4 tracking-tight">4. Nội dung bị cấm</h2>
          <p>
            Người dùng không được đăng tải nội dung vi phạm pháp luật, kích động bạo lực, phân biệt đối xử, hoặc xâm phạm quyền riêng tư của người khác. Nội dung vi phạm sẽ bị gỡ bỏ và tài khoản có thể bị khóa vĩnh viễn.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-bold text-black mb-4 tracking-tight">5. Giao dịch và thanh toán</h2>
          <p>
            Mọi giao dịch trên nền tảng được thực hiện thông qua hệ thống dl. Người dùng có trách nhiệm xác nhận giao dịch trước khi hoàn tất. Các giao dịch đã hoàn tất không được hoàn trả trừ trường hợp lỗi kỹ thuật từ phía hệ thống.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-bold text-black mb-4 tracking-tight">6. Quyền riêng tư và dữ liệu</h2>
          <p>
            DocLib thu thập và xử lý dữ liệu cá nhân theo quy định của pháp luật Việt Nam về bảo vệ dữ liệu. Người dùng có quyền yêu cầu xuất hoặc xóa dữ liệu cá nhân thông qua tính năng quản lý dữ liệu cá nhân trong phần cài đặt tài khoản.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-bold text-black mb-4 tracking-tight">7. Giới hạn trách nhiệm</h2>
          <p>
            DocLib cung cấp dịch vụ trên cơ sở hiện trạng. Chúng tôi không đảm bảo dịch vụ sẽ hoạt động liên tục, không gián đoạn hoặc không có lỗi. Trong mọi trường hợp, trách nhiệm của DocLib không vượt quá số tiền người dùng đã thanh toán cho dịch vụ.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-bold text-black mb-4 tracking-tight">8. Thay đổi điều khoản</h2>
          <p>
            DocLib có quyền cập nhật điều khoản sử dụng bất kỳ lúc nào. Người dùng sẽ được thông báo qua email hoặc thông báo hệ thống khi có thay đổi quan trọng. Việc tiếp tục sử dụng dịch vụ sau khi điều khoản được cập nhật đồng nghĩa với việc chấp nhận các thay đổi.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-bold text-black mb-4 tracking-tight">9. Liên hệ</h2>
          <p>
            Mọi thắc mắc về điều khoản sử dụng, vui lòng liên hệ qua email hỗ trợ được cung cấp trên trang chủ DocLib.
          </p>
        </section>
      </div>
    </div>
  );
}
