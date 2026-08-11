import {
  API_URL,
  getAuthHeaders,
} from "@/shared/services/api-client";

export async function updateUserShadowbanAPI(userId: string, status: boolean) {
  const response = await fetch(
    `${API_URL}/van-hanh/nguoi-dung/${userId}/cam-ngam`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    },
  );
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      payload.detail || payload.message || "Không thể cập nhật quyền hiển thị",
    );
  }
  return payload;
}

export async function updateUserKycAPI(
  userId: string,
  status: "PENDING" | "VERIFIED" | "REJECTED",
) {
  const response = await fetch(
    `${API_URL}/van-hanh/nguoi-dung/${userId}/xac-minh/${status}`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    },
  );
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      payload.detail ||
        payload.message ||
        "Không thể cập nhật xác minh danh tính",
    );
  }
  return payload;
}

