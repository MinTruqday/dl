import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export async function purchaseDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/kiem-tien/mua/tai-lieu`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || data.message || "Mua tài liệu thất bại");
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
    throw new Error(data.detail || data.message || "Failed to upgrade membership plan");
  }
  return data;
}
