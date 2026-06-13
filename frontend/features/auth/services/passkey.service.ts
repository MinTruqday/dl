import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function getPasskeyRegistrationOptionsAPI() {
  const res = await fetch(`${API_URL}/auth/passkey/options/register`, {
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải tùy chọn đăng ký khóa truy cập",
    );
  return data;
}

export async function verifyPasskeyRegistrationAPI(attestationResponse: any) {
  const res = await fetch(`${API_URL}/auth/passkey/auth/register`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(attestationResponse),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Xác thực đăng ký khóa truy cập thất bại");
  return data;
}

export async function getPasskeyLoginOptionsAPI(email: string) {
  const res = await fetch(
    `${API_URL}/auth/passkey/options/login?email=${encodeURIComponent(email)}`,
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tải tùy chọn đăng nhập khóa truy cập",
    );
  return data;
}

export async function verifyPasskeyLoginAPI(assertionResponse: any) {
  const res = await fetch(`${API_URL}/auth/passkey/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(assertionResponse),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Đăng nhập bằng khóa truy cập thất bại");
  return data;
}
