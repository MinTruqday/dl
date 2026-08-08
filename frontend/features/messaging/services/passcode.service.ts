const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const getToken = () => {
  if (typeof window !== "undefined") {
    return (
      localStorage.getItem("token") ||
      localStorage.getItem("access_token") ||
      sessionStorage.getItem("token") ||
      ""
    );
  }
  return "";
};

export const setPinLockAPI = async (otherUserId: string, pinCode: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/an-tin-nhan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ pin_code: pinCode }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi đặt mã PIN ẩn cuộc trò chuyện");
  return data;
};

export const verifyPinAPI = async (otherUserId: string, pinCode: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/xac-thuc-pin`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ pin_code: pinCode }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Mã PIN xác thực không đúng");
  return data;
};

export const removePinLockAPI = async (otherUserId: string, pinCode: string) => {
  const token = getToken();
  if (!token) throw new Error("Phiên đăng nhập đã hết hạn");
  const res = await fetch(`${API_URL}/tin-nhan/${otherUserId}/xoa-ma-pin`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ pin_code: pinCode }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi xóa mã PIN ẩn cuộc trò chuyện");
  return data;
};
