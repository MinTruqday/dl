# Kiến trúc frontend Veriq

Frontend dùng JavaScript hiện đại và giữ cùng ranh giới nghiệp vụ với các service đang hoạt động trong `backend/`

## Cấu trúc

```text
app/                       Route, layout và metadata của Next.js
features/<service>/
  pages/                   Màn hình hoàn chỉnh được route compose
  components/              Thành phần chỉ dùng trong feature
  hooks/                   Trạng thái tải, mutation và lỗi
  services/                Transport và endpoint
  lib/                     Quy tắc nghiệp vụ thuần của feature
shared/
  components/common/       Trạng thái và phản hồi dùng chung
  components/layout/       App shell, page header và điều hướng
  components/navigation/   Điều hướng cục bộ dùng chung
  components/ui/           Primitive tương tác
  contexts/                Context cấp ứng dụng
  services/                Kết nối API và xử lý phiên dùng chung
```

## Ánh xạ với backend

| Frontend feature | Backend service          | Phạm vi giao diện                    |
| ---------------- | ------------------------ | ------------------------------------ |
| `authentication` | `backend/authentication` | Phiên danh tính passkey và Google     |
| `cloud`          | `backend/cloud`          | Tải và lưu tệp                       |
| `legal`          | Không gọi service        | Nội dung điều khoản                  |
| `notification`   | `backend/notification`   | Thông báo                            |
| `testing`        | `backend/testing`        | Vòng đời kiểm thử và các tác vụ AI    |

## Quy tắc phụ thuộc

- `app/` chỉ compose page từ `features/` hoặc layout từ `shared/`.
- Component không gọi API trực tiếp.
- Hook sở hữu loading, mutation và lỗi; service sở hữu endpoint.
- Feature không import từ route trong `app/`.
- Chỉ mã dùng qua nhiều feature mới được đặt trong `shared/`.
- Tên file component dùng PascalCase hook dùng tiền tố `use` và service dùng hậu tố `.service.js`
- Route và nhãn điều hướng giữ nguyên để không phá hợp đồng URL.
- Route `page.jsx` chỉ import và export feature page không chứa state network hoặc nghiệp vụ
- Mã nguồn giữ cú pháp JavaScript hiện đại không chứa output transpile như `Object.assign` `void 0` hoặc helper `__rest`
- `pnpm quality` là cổng kiểm tra bắt buộc trước production build
