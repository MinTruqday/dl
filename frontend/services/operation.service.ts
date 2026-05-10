import { API_URL, getToken } from "./authentication.service";

export async function getAuthorApplicationsAPI(status: string = "PENDING") {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(
    `${API_URL}/van-hanh/don-ung-tuyen/tac-gia?status=${status}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách đơn ứng tuyển");
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
    `${API_URL}/van-hanh/don-ung-tuyen/tac-gia/${applicationId}/xet-duyet`,
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
  const res = await fetch(`${API_URL}/van-hanh/cau-hinh`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải cấu hình hệ thống");
  return data;
}

export async function getSystemHealthAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/van-hanh/suc-khoe-he-thong`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải sức khỏe hệ thống");
  return data;
}

export async function getCollectorStatsAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/van-hanh/thu-thap/thong-ke`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải chỉ số thu thập");
  return data;
}

export async function getMaintenanceModeAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/van-hanh/bao-tri`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải trạng thái bảo trì");
  return data;
}

export async function toggleMaintenanceModeAPI(
  enabled: boolean,
) {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/van-hanh/bao-tri?enabled=${enabled}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Thao tác chuyển đổi bảo trì thất bại");
  return data;
}

export async function triggerBackupAPI() {
  const token = getToken();
  if (!token) throw new Error("Bạn cần đăng nhập để thao tác");
  const res = await fetch(`${API_URL}/van-hanh/sao-luu`, {
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
  const res = await fetch(`${API_URL}/van-hanh/bao-cao`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Không thể tải danh sách báo cáo");
  return data;
}
