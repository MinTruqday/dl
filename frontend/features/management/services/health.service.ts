import {
  API_URL,
  getToken,
} from "@/features/authentication/services/session.service";

export async function getAuthorApplicationsAPI(status: string = "PENDING") {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(
    `${API_URL}/nguoi-dung/don-dang-ky/tac-gia?status=${status}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất danh sách hồ sơ đăng ký tác giả");
  return data;
}

export async function reviewAuthorApplicationAPI(
  applicationId: string,
  status: string,
  reason: string,
) {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(
    `${API_URL}/nguoi-dung/don-dang-ky/tac-gia/${applicationId}/xet-duyet`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status, reason }),
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi cập nhật trạng thái xét duyệt hồ sơ");
  return data;
}

export async function getAdminConfigAPI() {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/van-hanh/cai-dat`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất siêu dữ liệu cấu hình hệ thống");
  return data;
}

export async function updateAdminConfigAPI(config: any) {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/van-hanh/cai-dat`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(config),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi lưu trữ tham số cấu hình hệ thống");
  return data;
}

export async function getSystemHealthAPI() {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/van-hanh/tinh-trang`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi giám sát trạng thái sức khỏe hệ thống");
  return data;
}

export async function getMaintenanceModeAPI() {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/van-hanh/bao-tri`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất trạng thái bảo trì hệ thống");
  return data;
}

export async function toggleMaintenanceModeAPI(enabled: boolean) {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/van-hanh/bao-tri?enabled=${enabled}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi thay đổi trạng thái bảo trì hệ thống");
  return data;
}

export async function triggerBackupAPI() {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/van-hanh/sao-luu`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Lỗi khởi tạo tiến trình sao lưu dữ liệu");
  return data;
}

export async function getAdminReportsAPI() {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/van-hanh/bao-cao`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất danh sách báo cáo quản trị");
  return data;
}

export async function getMinioStatsAPI() {
  const token = getToken();
  if (!token) throw new Error("Yêu cầu xác thực tài khoản để thực hiện thao tác");
  const res = await fetch(`${API_URL}/van-hanh/luu-tru/thong-ke`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Lỗi trích xuất thông số lưu trữ hệ thống MinIO");
  return data;
}
