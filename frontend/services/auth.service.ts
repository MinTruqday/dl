export const API_URL = process.env.NEXT_PUBLIC_API_URL;

export function getToken() {
    if (typeof window !== 'undefined') {
        const t = localStorage.getItem('doclib_token');
        if (t === 'null' || t === 'undefined') return null;
        return t;
    }
    return null;
}

export function getAuthHeaders() {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export function setToken(token: string) {
    if (typeof window !== 'undefined') {
        localStorage.setItem('doclib_token', token);
        userMePromise = null;
    }
}

export function removeToken() {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('doclib_token');
        userMePromise = null;
    }
}

let userMePromise: Promise<any> | null = null;

export async function login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString()
    });

    const json = await res.json();
    if (!res.ok) throw new Error(json.message || "Đăng nhập thất bại.");
    return json.data;
}

export async function register(email: string, password: string, full_name: string, slug: string, agreed_to_terms: boolean) {
    const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, full_name, slug, agreed_to_terms })
    });

    const json = await res.json();
    if (!res.ok) throw new Error(json.message || "Đăng ký thất bại.");
    return json.data;
}

export async function getUserMe() {
    const token = getToken();
    if (!token) return null;

    if (userMePromise) return userMePromise;

    userMePromise = (async () => {
        try {
            const res = await fetch(`${API_URL}/auth/me`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
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
  const res = await fetch(`${API_URL}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  if (!res.ok) throw new Error("Yêu cầu khôi phục mật khẩu thất bại.");
  return res.json();
};

export const resetPasswordAPI = async (token: string, newPassword: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Đặt lại mật khẩu thất bại.");
  return data.data || data;
};

export const verifyCodeAPI = async (token: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/verify-code`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Mã xác thực không hợp lệ.");
  return data.data || data;
};

export const passkeyLoginBeginAPI = async (email: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/login/begin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Bắt đầu đăng nhập Passkey thất bại.");
  return data.data || data;
};

export const passkeyLoginFinishAPI = async (email: string, credential: any): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/login/finish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, credential })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Hoàn tất đăng nhập Passkey thất bại.");
  return data.data || data;
};

export const passkeyRegisterBeginAPI = async (email: string): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/register/begin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Bắt đầu đăng ký Passkey thất bại.");
  return data.data || data;
};

export const passkeyRegisterFinishAPI = async (email: string, credential: any): Promise<any> => {
  const res = await fetch(`${API_URL}/auth/passkey/register/finish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, credential })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || data.detail || "Hoàn tất đăng ký Passkey thất bại.");
  return data.data || data;
};
export const getGoogleLoginUrlAPI = async (): Promise<string> => {
  const res = await fetch(`${API_URL}/auth/google/login`);
  const data = await res.json();
  if (!res.ok || !data.data?.url) throw new Error("Không thể lấy liên kết đăng nhập Google.");
  return data.data.url;
};
