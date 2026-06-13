import { API_URL, getAuthHeaders } from "./authentication.service";

export async function compileDocumentAPI(documentId: string) {
  const res = await fetch(`${API_URL}/tai-lieu/${documentId}/bien-dich`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Biên dịch tài liệu thất bại");
  return data;
}
