import { API_URL, getToken } from "./auth.service";

export async function getLatexSnippetsAPI() {
  const res = await fetch(`${API_URL}/editor/latex`);
  if (!res.ok) throw new Error("Không thể tải danh sách snippets LaTeX.");
  const json = await res.json();
  return json.data?.snippets || [];
}

export async function compilePreviewAPI(
  content: string,
  is_fragment: boolean = true,
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/latex/compile-preview`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ content, is_fragment }),
  });
  if (!res.ok) throw new Error("Không thể hiển thị bản xem trước.");
  return await res.blob();
}

export async function getSynonymsAPI(word: string, context: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/inference/synonyms`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ word, context }),
  });
  if (!res.ok) throw new Error("Không tìm thấy từ đồng nghĩa phù hợp.");
  return await res.json();
}

export async function grammarCheckAPI(text: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/inference/grammar-check`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error("Lỗi kết nối máy chủ AI.");
  return await res.json();
}
