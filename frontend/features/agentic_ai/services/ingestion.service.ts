import {
  API_URL,
  getToken,
} from "@/features/authentication/services/session.service";

export async function ingestDocumentAPI(documentId: string) {
  const token = getToken();
  const res = await fetch(`${API_URL}/tiep-nap`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ document_id: documentId }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(
      data.message || "Không thể lập chỉ mục tài liệu",
    );
  return data;
}
