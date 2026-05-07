import { API_URL, getAuthHeaders } from "./authentication.service";

export async function translateTextAPI(text: string, targetLang: string = "vi") {
  const res = await fetch(`${API_URL}/suy-luan/dich-thuat`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Dịch thuật thất bại");
  return data;
}

export async function generateAICoverAPI(documentId: string) {
  const res = await fetch(`${API_URL}/suy-luan/tao-anh-bia`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo ảnh bìa AI thất bại");
  return data;
}

export async function analyzeSentimentAPI(text: string) {
  const res = await fetch(`${API_URL}/suy-luan/phan-tich-cam-xuc`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Phân tích cảm xúc thất bại");
  return data;
}

export async function grammarCheckAPI(text: string) {
  const res = await fetch(`${API_URL}/suy-luan/kiem-tra-ngu-phap`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Kiểm tra ngữ pháp thất bại");
  return data;
}

export async function getSynonymsAPI(text: string) {
  const res = await fetch(`${API_URL}/suy-luan/tu-dong-nghia`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tìm từ đồng nghĩa thất bại");
  return data;
}

export async function generateCodeAPI(prompt: string) {
  const res = await fetch(`${API_URL}/suy-luan/tao-ma-nguon`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo mã nguồn thất bại");
  return data;
}
