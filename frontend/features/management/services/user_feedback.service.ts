import {
  API_URL,
  getAuthHeaders,
} from "@/features/authentication/services/session.service";

export async function submitReportAPI(payload: {
  item_type: string;
  item_id: string;
  reason: string;
  description?: string;
}) {
  const res = await fetch(`${API_URL}/phan-hoi/phan-hoi`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: payload.item_id,
      message_id: payload.item_type,
      vote_type: "report",
      comment: [payload.reason, payload.description].filter(Boolean).join("\n"),
    }),
  });
  const data = await res.json();
  if (!res.ok)
    throw new Error(data.message || "Không thể tạo yêu cầu báo cáo vi phạm");
  return data;
}
