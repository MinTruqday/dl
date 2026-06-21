import { API_URL, getAuthHeaders } from "@/features/auth/services/user_authentication.service";

export async function translateTextAPI(
  text: string,
  targetLang: string = "vi",
) {
  const res = await fetch(`${API_URL}/inference/dich-thuat`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Dịch thuật thất bại");
  return data;
}


export async function grammarCheckAPI(text: string) {
  const res = await fetch(`${API_URL}/inference/grammar-check`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Kiểm tra ngữ pháp thất bại");
  return data;
}

export async function getSynonymsAPI(text: string) {
  const res = await fetch(`${API_URL}/inference/tu-dong-nghia`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tìm từ đồng nghĩa thất bại");
  return data;
}

export async function generateCodeAPI(prompt: string) {
  const res = await fetch(`${API_URL}/inference/tao-ma`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Tạo mã nguồn thất bại");
  return data;
}
