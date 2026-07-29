export const API_URL = process.env.NEXT_PUBLIC_API_URL;
export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (API_URL ? API_URL.replace("http", "ws") : "");

export function getToken() {
  if (typeof window !== "undefined") {
    const t = localStorage.getItem("doclib_token");
    if (t === "null" || t === "undefined") return null;
    return t;
  }
  return null;
}

export function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function setToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("doclib_token", token);
    userMePromise = null;
  }
}

export function removeToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("doclib_token");
    userMePromise = null;
  }
}

let userMePromise: Promise<any> | null = null;

export async function login(email: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${API_URL}/xac-thuc/dang-nhap`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  });

  const json = await res.json();
  if (!res.ok)
    throw new Error(json.detail || json.message || "Lỗi xác thực thông tin đăng nhập");
  return json.data;
}

export async function register(
  email: string,
  password: string,
  full_name: string,
  slug: string,
  agreed_to_terms: boolean,
) {
  const res = await fetch(`${API_URL}/xac-thuc/dang-ky`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password, full_name, slug, agreed_to_terms }),
  });

  const json = await res.json();
  if (!res.ok)
    throw new Error(json.detail || json.message || "Lỗi khởi tạo hồ sơ người dùng mới");
  return json.data;
}

export async function getUserMe() {
  const token = getToken();
  if (!token) return null;

  if (userMePromise) return userMePromise;

  userMePromise = (async () => {
    try {
      const res = await fetch(`${API_URL}/xac-thuc/ca-nhan`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        removeToken();
        return null;
      }
      const json = await res.json();
      return json.data;
    } finally {
      userMePromise = null;
    }
  })();
  return userMePromise;
}

export const forgotPasswordAPI = async (email: string): Promise<any> => {
  const res = await fetch(`${API_URL}/xac-thuc/quen-mat-khau`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) throw new Error("Lỗi khởi tạo tiến trình khôi phục mật khẩu");
  return res.json();
};

export const resetPasswordAPI = async (
  token: string,
  newPassword: string,
): Promise<any> => {
  const res = await fetch(`${API_URL}/xac-thuc/dat-lai-mat-khau`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || data.detail || "Lỗi cập nhật cấu trúc mật khẩu mới");
  return data.data || data;
};

export const verifyCodeAPI = async (token: string): Promise<any> => {
  const res = await fetch(`${API_URL}/xac-thuc/xac-nhan-ma`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || data.detail || "Lỗi sai lệch mã thông báo xác thực");
  return data.data || data;
};

export const passkeyLoginBeginAPI = async (email: string): Promise<any> => {
  const res = await fetch(
    `${API_URL}/xac-thuc/khoa-bao-mat/dang-nhap/bat-dau`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || data.detail || "Lỗi khởi tạo luồng đăng nhập chứng thư số",
    );
  return data.data || data;
};

export const passkeyLoginFinishAPI = async (
  email: string,
  credential: any,
): Promise<any> => {
  const res = await fetch(
    `${API_URL}/xac-thuc/khoa-bao-mat/dang-nhap/hoan-tat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, credential }),
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || data.detail || "Lỗi hoàn tất luồng đăng nhập chứng thư số",
    );
  return data.data || data;
};

export const passkeyRegisterBeginAPI = async (email: string): Promise<any> => {
  const res = await fetch(`${API_URL}/xac-thuc/khoa-bao-mat/dang-ky/bat-dau`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || data.detail || "Lỗi khởi tạo luồng đăng ký chứng thư số",
    );
  return data.data || data;
};

export const passkeyRegisterFinishAPI = async (
  email: string,
  credential: any,
): Promise<any> => {
  const res = await fetch(`${API_URL}/xac-thuc/khoa-bao-mat/dang-ky/hoan-tat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, credential }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || data.detail || "Lỗi hoàn tất luồng đăng ký chứng thư số",
    );
  return data.data || data;
};
export const getGoogleLoginUrlAPI = async (): Promise<string> => {
  const res = await fetch(`${API_URL}/xac-thuc/google/dang-nhap`);
  const data = await res.json();
  if (!res.ok || !data.data?.url)
    throw new Error("Lỗi truy xuất điểm cuối xác thực định danh Google");
  return data.data.url;
};

export const finishGoogleLoginAPI = async (
  code: string,
  state: string,
): Promise<any> => {
  const query = new URLSearchParams({ code, state });
  const res = await fetch(`${API_URL}/google/callback?${query.toString()}`);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.message || data.detail || "Không thể xác thực Google");
  }
  return data.data || data;
};
