import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function getPasskeyRegistrationOptionsAPI() {
  const res = await fetch(`${API_URL}/xac-thuc/khoa-bao-mat/dang-ky/bat-dau`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Lỗi truy xuất tham số cấu hình đăng ký chứng thư số",
    );
  return data;
}

export async function verifyPasskeyRegistrationAPI(attestationResponse: any) {
  const res = await fetch(`${API_URL}/xac-thuc/khoa-bao-mat/dang-ky/hoan-tat`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(attestationResponse),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi kiểm chứng kết quả đăng ký chứng thư số");
  return data;
}

export async function getPasskeyLoginOptionsAPI(email: string) {
  const res = await fetch(
    `${API_URL}/xac-thuc/khoa-bao-mat/dang-nhap/bat-dau?email=${encodeURIComponent(email)}`,
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Lỗi truy xuất tham số cấu hình đăng nhập chứng thư số",
    );
  return data;
}

export async function verifyPasskeyLoginAPI(assertionResponse: any) {
  const res = await fetch(
    `${API_URL}/xac-thuc/khoa-bao-mat/dang-nhap/hoan-tat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(assertionResponse),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi kiểm chứng dữ liệu đăng nhập chứng thư số");
  return data;
}
