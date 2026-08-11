import {
  API_URL,
  getAuthHeaders,
} from "@/shared/services/api-client";

export type DrmSettings = {
  disable_copy: boolean;
  disable_print: boolean;
  hide_from_search: boolean;
  watermark_enabled: boolean;
  allow_internal_ai: boolean;
  license_valid_days: number;
  max_open_count: number;
  ghost_font_enabled: boolean;
  ghost_font_exemption_scope:
    | "owner_only"
    | "private_link"
    | "selected_users"
    | "everyone";
  ghost_font_exempt_user_ids: string[];
};

export async function updateDRMSettingsAPI(
  documentId: string,
  settings: DrmSettings,
) {
  const response = await fetch(`${API_URL}/ban-quyen/${documentId}`, {
    method: "PUT",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      payload.detail || payload.message || "Không thể cấu hình bảo vệ tài liệu",
    );
  }
  return payload;
}

