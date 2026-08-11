"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/shared/components/ui/Button";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import {
  connectMcpPresetAPI,
  getMcpPresetsAPI,
  getMcpServersAPI,
  McpPreset,
  probeMcpServerAPI,
  registerMcpServerAPI,
} from "../services/mcp.service";

export default function McpPresetModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [presets, setPresets] = useState<McpPreset[]>([]);
  const [servers, setServers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [connecting, setConnecting] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [customName, setCustomName] = useState("");
  const [customDescription, setCustomDescription] = useState("");
  const [customUrl, setCustomUrl] = useState("");
  const [customToken, setCustomToken] = useState("");
  const [customTransport, setCustomTransport] = useState<"streamable_http" | "sse">("streamable_http");
  useNoticeToast(error, "error");
  useNoticeToast(notice);

  const connected = useMemo(
    () => new Set(servers.map((server) => String(server.preset_id || ""))),
    [servers],
  );
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [presetRows, serverRows] = await Promise.all([
        getMcpPresetsAPI(),
        getMcpServersAPI(),
      ]);
      setPresets(presetRows);
      setServers(serverRows);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không thể tải MCP");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) void load();
  }, [load, open]);
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/25 p-4" role="dialog" aria-modal="true" aria-labelledby="mcp-title">
      <div className="max-h-[85vh] w-full max-w-3xl overflow-y-auto rounded-panel border border-border bg-surface p-5 shadow-xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="mcp-title" className="text-[18px] font-semibold text-ink">Kết nối MCP</h2>
            <p className="mt-1 text-[13px] leading-5 text-ink-muted">
              Dùng lựa chọn có sẵn hoặc kết nối máy chủ của bạn
            </p>
          </div>
          <Button type="button" variant="ghost" onClick={onClose}>Đóng</Button>
        </div>

        <section className="mt-5 rounded-panel border border-border p-4">
          <h3 className="text-[15px] font-semibold text-ink">Máy chủ của bạn</h3>
          <p className="mt-1 text-[12px] text-ink-muted">Máy chủ chỉ được lưu sau khi kết nối và đọc được công cụ</p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="text-[12px] font-medium text-ink">
              Tên máy chủ
              <input className="apple-input mt-1 w-full" value={customName} onChange={(event) => setCustomName(event.target.value)} />
            </label>
            <label className="text-[12px] font-medium text-ink">
              Cách kết nối
              <select className="apple-input mt-1 w-full" value={customTransport} onChange={(event) => setCustomTransport(event.target.value as "streamable_http" | "sse")}>
                <option value="streamable_http">Kết nối truyền liên tục</option>
                <option value="sse">Kết nối sự kiện máy chủ</option>
              </select>
            </label>
            <label className="text-[12px] font-medium text-ink sm:col-span-2">
              Mô tả khả năng
              <input className="apple-input mt-1 w-full" value={customDescription} onChange={(event) => setCustomDescription(event.target.value)} />
            </label>
            <label className="text-[12px] font-medium text-ink sm:col-span-2">
              Địa chỉ máy chủ
              <input className="apple-input mt-1 w-full" value={customUrl} onChange={(event) => setCustomUrl(event.target.value)} placeholder="https://mcp.example.com" inputMode="url" />
            </label>
            <label className="text-[12px] font-medium text-ink sm:col-span-2">
              Mã truy cập không bắt buộc
              <input className="apple-input mt-1 w-full" type="password" value={customToken} onChange={(event) => setCustomToken(event.target.value)} autoComplete="off" />
            </label>
          </div>
          <Button
            type="button"
            className="mt-4"
            disabled={!customName.trim() || !customDescription.trim() || !customUrl.trim() || Boolean(connecting)}
            onClick={async () => {
              setConnecting("custom");
              setError("");
              try {
                await registerMcpServerAPI({
                  name: customName.trim(),
                  description: customDescription.trim(),
                  server_type: customTransport,
                  url: customUrl.trim(),
                  auth_token: customToken.trim() || undefined,
                });
                setCustomName("");
                setCustomDescription("");
                setCustomUrl("");
                setCustomToken("");
                setNotice("Đã kết nối máy chủ của bạn");
                await load();
              } catch (reason) {
                setError(reason instanceof Error ? reason.message : "Không thể kết nối MCP");
              } finally {
                setConnecting("");
              }
            }}
          >
            {connecting === "custom" ? "Đang kiểm tra" : "Kiểm tra và kết nối"}
          </Button>
        </section>

        {servers.some((server) => !server.preset_id) && (
          <section className="mt-5">
            <h3 className="mb-3 text-[15px] font-semibold text-ink">Kết nối của bạn</h3>
            <div className="space-y-2">
              {servers.filter((server) => !server.preset_id).map((server) => {
                const id = String(server._id || server.id);
                return (
                  <div key={id} className="flex items-center justify-between gap-4 rounded-panel border border-border p-3">
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-semibold text-ink">{server.name}</p>
                      <p className="mt-1 text-[12px] text-ink-muted">
                        {server.is_connected ? `${server.tool_names?.length || 0} công cụ đã sẵn sàng` : "Chưa kết nối"}
                      </p>
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      disabled={Boolean(connecting)}
                      onClick={async () => {
                        setConnecting(id);
                        setError("");
                        try {
                          await probeMcpServerAPI(id);
                          setNotice(`Đã kiểm tra ${server.name}`);
                          await load();
                        } catch (reason) {
                          setError(reason instanceof Error ? reason.message : "Không thể kiểm tra MCP");
                        } finally {
                          setConnecting("");
                        }
                      }}
                    >
                      {connecting === id ? "Đang kiểm tra" : "Kiểm tra lại"}
                    </Button>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        <div className="mt-5 space-y-3">
          <h3 className="text-[15px] font-semibold text-ink">Lựa chọn có sẵn</h3>
          {loading ? (
            <p className="py-8 text-center text-[13px] text-ink-muted">Đang kiểm tra máy chủ</p>
          ) : presets.length ? (
            presets.map((preset) => {
              const isConnected = connected.has(preset.id);
              return (
                <article key={preset.id} className="rounded-panel border border-border p-4">
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-[15px] font-semibold text-ink">{preset.name}</h3>
                        <span className="rounded-control bg-success-soft px-2 py-0.5 text-[11px] font-medium text-success">Đã kiểm tra</span>
                      </div>
                      <p className="mt-2 text-[13px] leading-5 text-ink-muted">{preset.description}</p>
                      <p className="mt-2 text-[12px] text-ink-muted">{preset.tool_count} công cụ</p>
                      <p className="mt-1 text-[12px] text-ink-muted">{preset.setup_note}</p>
                      <a className="mt-2 inline-block text-[12px] font-medium text-brand hover:underline" href={preset.source_url} target="_blank" rel="noreferrer">Xem nguồn</a>
                    </div>
                    <Button
                      type="button"
                      className="shrink-0"
                      variant={isConnected ? "secondary" : "primary"}
                      disabled={isConnected || Boolean(connecting)}
                      onClick={async () => {
                        setConnecting(preset.id);
                        setError("");
                        try {
                          await connectMcpPresetAPI(preset.id);
                          setNotice(`Đã kết nối ${preset.name}`);
                          await load();
                        } catch (reason) {
                          setError(reason instanceof Error ? reason.message : "Không thể kết nối MCP");
                        } finally {
                          setConnecting("");
                        }
                      }}
                    >
                      {isConnected ? "Đã kết nối" : connecting === preset.id ? "Đang kết nối" : "Kết nối"}
                    </Button>
                  </div>
                </article>
              );
            })
          ) : (
            <p className="py-8 text-center text-[13px] text-ink-muted">Không có máy chủ nào vượt qua kiểm tra kết nối</p>
          )}
        </div>
      </div>
    </div>
  );
}
