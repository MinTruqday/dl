import {
  API_URL,
  getToken,
} from "@/shared/services/api-client";

function headers() {
  return {
    Authorization: `Bearer ${getToken()}`,
    "Content-Type": "application/json",
  };
}

export type McpPreset = {
  id: string;
  name: string;
  description: string;
  source_url: string;
  setup_note: string;
  tool_count: number;
  tool_names: string[];
  verified: true;
};

const mcpErrors: Record<string, string> = {
  mcp_requires_pro: "Tính năng MCP cần gói Chuyên sâu hoặc Toàn năng",
  mcp_preset_unavailable: "Máy chủ MCP chưa vượt qua kiểm tra kết nối",
  mcp_connection_failed: "Không thể kết nối máy chủ MCP",
  mcp_connector_already_exists: "Máy chủ MCP này đã được kết nối",
};

function errorMessage(data: any, fallback: string) {
  const code = String(data?.detail?.code || data?.detail || "");
  return mcpErrors[code] || fallback;
}

export async function getMcpPresetsAPI(): Promise<McpPreset[]> {
  const response = await fetch(`${API_URL}/mcp/presets`, { headers: headers() });
  const data = await response.json();
  if (!response.ok) throw new Error(errorMessage(data, "Không thể tải lựa chọn MCP"));
  return data.presets ?? [];
}

export async function connectMcpPresetAPI(presetId: string) {
  const response = await fetch(`${API_URL}/mcp/presets/${presetId}/connect`, {
    method: "POST",
    headers: headers(),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(errorMessage(data, "Không thể kết nối MCP"));
  return data;
}

export async function getMcpServersAPI() {
  const response = await fetch(`${API_URL}/mcp/servers`, { headers: headers() });
  const data = await response.json();
  if (!response.ok) throw new Error(errorMessage(data, "Không thể tải MCP"));
  return data.servers ?? [];
}

export async function registerMcpServerAPI(values: {
  name: string;
  description: string;
  server_type: "sse" | "streamable_http" | "stdio";
  url?: string;
  command?: string;
  args?: string[];
  auth_token?: string;
}) {
  const response = await fetch(`${API_URL}/mcp/servers`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(values),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(errorMessage(data, "Không thể kết nối MCP"));
  return data;
}

export async function probeMcpServerAPI(id: string) {
  const response = await fetch(`${API_URL}/mcp/servers/${id}/kiem-tra`, {
    method: "POST",
    headers: headers(),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(errorMessage(data, "Không thể kiểm tra MCP"));
  return data;
}
