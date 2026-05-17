import { API_URL, getAuthHeaders } from "./authentication.service";

export async function uploadAssetAPI(file: File, type: string = "document") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("type", type);

  const res = await fetch(`${API_URL}/tai-len/tap-tin`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tải tập tin lên thất bại");
  return data;
}

export async function uploadDocumentAPI(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/tai-len/tai-lieu`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tải tài liệu lên thất bại");
  return data;
}
