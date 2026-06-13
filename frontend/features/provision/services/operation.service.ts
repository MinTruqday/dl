import { API_URL, getToken } from "@/features/auth/services/authentication.service";

export async function getAuthorApplicationsAPI(status: string = "PENDING") {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(
    `${API_URL}/hoat-dong/don-dang-ky/tac-gia?status=${status}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách đơn ứng tuyển");
  return data;
}

export async function reviewAuthorApplicationAPI(
  applicationId: string,
  status: string,
  reason: string,
) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(
    `${API_URL}/hoat-dong/don-dang-ky/tac-gia/${applicationId}/xet-duyet`,
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
  if (!res.ok) throw new Error(data.message || "Thao tác xử lý hồ sơ thất bại");
  return data;
}

export async function getAdminConfigAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/hoat-dong/config`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải cấu hình hệ thống");
  return data;
}

export async function updateAdminConfigAPI(config: any) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/hoat-dong/config`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(config),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể cập nhật cấu hình hệ thống");
  return data;
}

export async function getSystemHealthAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/hoat-dong/system-health`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải sức khỏe hệ thống");
  return data;
}

export async function getMaintenanceModeAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/hoat-dong/maintenance`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải trạng thái bảo trì");
  return data;
}

export async function toggleMaintenanceModeAPI(enabled: boolean) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/hoat-dong/maintenance?enabled=${enabled}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Thao tác chuyển đổi bảo trì thất bại");
  return data;
}

export async function triggerBackupAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/hoat-dong/backup`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Khởi tạo sao lưu thất bại");
  return data;
}

export async function getAdminReportsAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/hoat-dong/bao-cao`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải danh sách báo cáo");
  return data;
}

export async function getMinioStatsAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/hoat-dong/minio/thong-ke`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tải thông số lưu trữ MinIO");
  return data;
}
