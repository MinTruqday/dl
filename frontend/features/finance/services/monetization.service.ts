import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function purchaseDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/kiem-tien/mua/tai-lieu`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(
      data.detail || data.message || "Lỗi giao dịch mua tài liệu",
    );
  }
  return data;
}

export async function buyMembershipAPI(tier: "PRO" | "PREMIUM") {
  const res = await fetch(`${API_URL}/kiem-tien/thanh-vien`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ tier }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(
      data.detail || data.message || "Lỗi xử lý yêu cầu nâng cấp gói dịch vụ",
    );
  }
  return data;
}

export async function getMembershipPricingAPI() {
  const res = await fetch(`${API_URL}/kiem-tien/bang-gia`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Không thể tải bảng giá");
  }
  return data;
}

export async function getAuthorRevenueAPI() {
  const res = await fetch(`${API_URL}/kiem-tien/doanh-thu`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(
      data.detail || data.message || "Không thể tải số liệu doanh thu",
    );
  }
  return data;
}

export async function setDocumentPricingAPI(
  documentId: string,
  priceDl: number,
  isDrmProtected: boolean = true,
) {
  const res = await fetch(`${API_URL}/kiem-tien/thiet-lap-gia`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      document_id: documentId,
      price_dl: priceDl,
      is_drm_protected: isDrmProtected,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(
      data.detail || data.message || "Không thể cập nhật cấu hình định giá",
    );
  }
  return data;
}
