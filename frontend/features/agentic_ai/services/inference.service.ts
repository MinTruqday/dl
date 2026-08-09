import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function translateTextAPI(
  text: string,
  targetLang: string = "vi",
) {
  const res = await fetch(`${API_URL}/suy-luan/dich-thuat`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text, target_lang: targetLang }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể dịch nội dung",
    );
  return data;
}

export async function grammarCheckAPI(text: string) {
  const res = await fetch(`${API_URL}/suy-luan/kiem-tra-ngu-phap`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể kiểm tra ngữ pháp",
    );
  return data;
}

export async function getSynonymsAPI(text: string) {
  const res = await fetch(`${API_URL}/suy-luan/tu-dong-nghia`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tìm từ đồng nghĩa",
    );
  return data;
}

export async function generateCodeAPI(prompt: string) {
  const res = await fetch(`${API_URL}/suy-luan/tao-ma-nguon`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể tạo mã nguồn",
    );
  return data;
}

async function postInference(path: string, body: object) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : data.message || "Không thể xử lý nội dung",
    );
  return data;
}

export const summarizeTextAPI = (text: string) =>
  postInference("/suy-luan/tom-tat", { text, language: "vi" });

export const extractGlossaryAPI = (text: string) =>
  postInference("/suy-luan/giai-thich-thuat-ngu", { text });

export const factCheckTextAPI = (text: string) =>
  postInference("/suy-luan/kiem-chung-su-that", { text });

export const checkPlagiarismAPI = (content: string) =>
  postInference("/suy-luan/kiem-tra-dao-van", { content });
