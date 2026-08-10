"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/shared/components/ui/Button";
import { useNoticeToast } from "@/shared/hooks/useNoticeToast";
import {
  connectMcpPresetAPI,
  getMcpPresetsAPI,
  getMcpServersAPI,
  McpPreset,
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
      <div className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-panel border border-border bg-surface p-5 shadow-xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="mcp-title" className="text-[18px] font-semibold text-ink">Kết nối MCP</h2>
            <p className="mt-1 text-[13px] leading-5 text-ink-muted">
              Chỉ hiển thị máy chủ đã khởi tạo thành công và trả về danh sách công cụ.
            </p>
          </div>
          <Button type="button" variant="ghost" onClick={onClose}>Đóng</Button>
        </div>

        <div className="mt-5 space-y-3">
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
                      <p className="mt-2 text-[12px] text-ink-muted">{preset.tool_count} công cụ · {preset.setup_note}</p>
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
