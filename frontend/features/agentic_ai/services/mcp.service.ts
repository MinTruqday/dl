import {
  API_URL,
  getToken,
} from "@/features/authentication/services/session.service";

function headers() {
  return {
    Authorization: `Bearer ${getToken()}`,
    "Content-Type": "application/json",
  };
}

export async function getMcpServersAPI() {
  const response = await fetch(`${API_URL}/mcp/servers`, { headers: headers() });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail?.code || data.detail || "Không thể tải MCP");
  return data.servers ?? [];
}

export async function registerMcpServerAPI(values: {
  name: string;
  description: string;
  url: string;
}) {
  const response = await fetch(`${API_URL}/mcp/servers`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ ...values, server_type: "sse", args: [] }),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.detail?.code || data.detail || "Không thể kết nối MCP");
  return data;
}

export async function probeMcpServerAPI(id: string) {
  const response = await fetch(`${API_URL}/mcp/servers/${id}/kiem-tra`, {
    method: "POST",
    headers: headers(),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.detail?.code || data.detail || "Không thể kiểm tra MCP");
  return data;
}
