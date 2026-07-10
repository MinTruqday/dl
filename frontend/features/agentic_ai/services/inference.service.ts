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
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Translation inference failed");
  return data;
}

export async function grammarCheckAPI(text: string) {
  const res = await fetch(`${API_URL}/suy-luan/kiem-tra-ngu-phap`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Grammar analysis inference failed");
  return data;
}

export async function getSynonymsAPI(text: string) {
  const res = await fetch(`${API_URL}/suy-luan/tu-dong-nghia`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Synonym extraction failed");
  return data;
}

export async function generateCodeAPI(prompt: string) {
  const res = await fetch(`${API_URL}/suy-luan/tao-ma`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "MODULE AGENTIC_AI: Code generation inference failed");
  return data;
}
