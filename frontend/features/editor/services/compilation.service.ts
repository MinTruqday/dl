import { API_URL, getAuthHeaders } from "@/features/auth/services/authentication.service";

export async function compileDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/document/${documentId}/compile`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Biên dịch tài liệu thất bại");
  return data;
}
