"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  clearUserInstructionsAPI,
  cancelAiExecutionAPI,
  createAiSessionAPI,
  deleteAiSessionAPI,
  getAiSessionAPI,
  getAiSessionsAPI,
  getAiWorkspaceAPI,
  getPendingAiApprovalsAPI,
  getUserInstructionsAPI,
  saveUserInstructionsAPI,
  resolveAiApprovalAPI,
  streamAiChatAPI,
  updateAiSessionTitleAPI,
} from "@/features/agentic_ai/services/interaction.service";
import { uploadChatAttachmentAPI } from "@/features/cloud/services/upload.service";
import {
  getMyQuotaAPI,
  QuotaUsage,
} from "@/features/usage/services/quota.service";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  attachment?: string;
};
export type ChatMode = "chat" | "work" | "goal" | "learn" | "plan";
export type ChatPlanStep = {
  id: string;
  task: string;
  status: "pending" | "running" | "completed" | "failed";
};
export type ChatApproval = {
  intervention_id: string;
  action_type: string;
  description: string;
  risk_level: "low" | "medium" | "high" | "critical";
};

const streamErrors: Record<string, string> = {
  ai_quota_exceeded: "Đã sử dụng hết hạn mức AI",
  quota_service_unavailable: "Không thể kiểm tra hạn mức AI",
  upload_quota_exceeded: "Đã sử dụng hết hạn mức tải lên",
  upload_quota_verification_failed: "Không thể kiểm tra hạn mức tải lên",
  document_access_denied: "Không có quyền đọc tài liệu",
  document_access_verification_failed: "Không thể xác minh quyền tài liệu",
  input_security_blocked: "Yêu cầu bị chặn bởi chính sách an toàn",
  planning_model_failed: "Không thể lập kế hoạch",
  orchestration_failed: "Không thể thực hiện kế hoạch",
  response_verification_failed: "Kết quả không vượt qua bước kiểm chứng",
  chat_stream_failed: "Luồng phản hồi bị gián đoạn",
  advanced_mode_requires_pro: "Chế độ này cần gói Pro hoặc Premium",
  multimodal_processing_failed: "Không thể xử lý tệp đa phương tiện",
};

function readDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Không thể đọc tệp đính kèm"));
    reader.readAsDataURL(file);
  });
}
export function useChat(documentId?: string | null) {
  const { user, isLoading: authLoading } = useAuth();
  const [sessions, setSessions] = useState<any[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [quota, setQuota] = useState<QuotaUsage | null>(null);
  const [instructions, setInstructions] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [planSteps, setPlanSteps] = useState<ChatPlanStep[]>([]);
  const [openedMode, setOpenedMode] = useState<ChatMode | null>(null);
  const [approvals, setApprovals] = useState<ChatApproval[]>([]);
  const requestController = useRef<AbortController | null>(null);
  const reload = useCallback(async () => {
    if (!user) return setLoading(false);
    setLoading(true);
    try {
      const [sessionResponse, quotaResponse, instructionResponse] =
        await Promise.all([
          getAiSessionsAPI(undefined, user._id),
          getMyQuotaAPI(),
          getUserInstructionsAPI(),
        ]);
      setSessions(sessionResponse.data ?? sessionResponse ?? []);
      setQuota(quotaResponse);
      setInstructions(
        instructionResponse.data?.instructions ??
          instructionResponse.instructions ??
          "",
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể tải trò chuyện",
      );
    } finally {
      setLoading(false);
    }
  }, [user]);
  useEffect(() => void reload(), [reload]);
  const newChat = () => {
    setSessionId(null);
    setMessages([]);
    setPlanSteps([]);
    setOpenedMode(null);
    setApprovals([]);
    setError("");
  };
  const openSession = async (id: string) => {
    setLoading(true);
    setError("");
    try {
      const [response, workspace] = await Promise.all([
        getAiSessionAPI(id),
        getAiWorkspaceAPI(id),
      ]);
      const row = response.data ?? response;
      setSessionId(id);
      setOpenedMode((workspace?.mode ?? row.mode ?? "chat") as ChatMode);
      setPlanSteps(
        (workspace?.steps ?? []).map((step: any) => ({
          id: String(step.id),
          task: String(step.task ?? ""),
          status: step.status ?? "pending",
        })),
      );
      setMessages(
        (row.messages ?? row.history ?? []).map((message: any) => ({
          id: message.id ?? message._id ?? crypto.randomUUID(),
          role: message.role,
          content: message.content ?? message.text ?? "",
        })),
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể mở phiên trò chuyện",
      );
    } finally {
      setLoading(false);
    }
  };
  const removeSession = async (id: string) => {
    try {
      await deleteAiSessionAPI(id);
      if (sessionId === id) newChat();
      await reload();
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Không thể xóa phiên trò chuyện",
      );
    }
  };
  const renameSession = async (id: string, title: string) => {
    try {
      await updateAiSessionTitleAPI(id, title.trim());
      await reload();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể đổi tên phiên",
      );
    }
  };
  const saveInstructions = async (value: string) => {
    try {
      if (value.trim()) await saveUserInstructionsAPI(value.trim());
      else await clearUserInstructionsAPI();
      setInstructions(value.trim());
      setNotice("Đã lưu chỉ dẫn cá nhân");
      return true;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể lưu chỉ dẫn",
      );
      return false;
    }
  };
  const send = async (
    text: string,
    mode: ChatMode,
    approvalPolicy: "manual" | "auto_safe",
    file?: File | null,
  ) => {
    if ((!text.trim() && !file) || sending) return false;
    setSending(true);
    setError("");
    let activeSession = sessionId;
    let approvalTimer: ReturnType<typeof setInterval> | null = null;
    try {
      const effectiveText =
        text.trim() ||
        (file?.type.startsWith("audio/")
          ? "Phân tích nội dung âm thanh đính kèm"
          : file?.type.startsWith("image/")
            ? "Phân tích nội dung hình ảnh đính kèm"
            : "Phân tích tệp đính kèm");
      if (!activeSession) {
        const created = await createAiSessionAPI("", effectiveText, mode);
        activeSession = created.data?._id ?? created._id;
        setSessionId(activeSession);
        setOpenedMode(mode);
        setPlanSteps([]);
      }
      const refreshApprovals = async () => {
        if (!activeSession) return;
        const rows = await getPendingAiApprovalsAPI(activeSession).catch(
          () => [],
        );
        setApprovals(rows);
      };
      approvalTimer = setInterval(() => void refreshApprovals(), 750);
      void refreshApprovals();
      let attachment: any = null;
      if (file) {
        const uploaded = await uploadChatAttachmentAPI(file);
        attachment = {
          url: uploaded.data?.url,
          filename: file.name,
          content_type: file.type || "application/octet-stream",
          size: file.size,
        };
      }
      const multimodalData =
        file && (file.type.startsWith("image/") || file.type.startsWith("audio/"))
          ? await readDataUrl(file)
          : null;
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: effectiveText,
        attachment: file?.name,
      };
      const assistantId = crypto.randomUUID();
      setMessages((rows) => [
        ...rows,
        userMessage,
        { id: assistantId, role: "assistant", content: "" },
      ]);
      requestController.current = new AbortController();
      const response = await streamAiChatAPI(
        {
          query: effectiveText,
          thinking: mode === "work" || mode === "goal",
          mode,
          approval_policy: approvalPolicy,
          session_id: activeSession,
          conversation_history: messages.slice(-8),
          user_id: user?._id,
          document_ids: documentId ? [documentId] : [],
          attachments: attachment ? [attachment] : [],
          image_data: file?.type.startsWith("image/") ? multimodalData : null,
          audio_data: file?.type.startsWith("audio/") ? multimodalData : null,
        },
        requestController.current.signal,
      );
      if (!response.ok || !response.body) {
        const body = await response.json().catch(() => ({}));
        throw new Error(
          body.message || body.detail || "Dịch vụ AI không phản hồi",
        );
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let answer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";
        for (const event of events) {
          const lines = event.split("\n");
          const type = lines
            .find((line) => line.startsWith("event:"))
            ?.slice(6)
            .trim();
          const data = lines
            .find((line) => line.startsWith("data:"))
            ?.slice(5)
            .trim();
          if (!data || type === "done" || data === "[DONE]") continue;
          try {
            const parsed = JSON.parse(data);
            if (type === "message" || !type)
              answer += parsed.chunk ?? parsed.answer ?? "";
            if (type === "plan" && Array.isArray(parsed.steps))
              setPlanSteps(
                parsed.steps.map((step: any, index: number) => ({
                  id: String(step.id ?? index + 1),
                  task: String(step.task ?? ""),
                  status: step.status ?? "pending",
                })),
              );
            if (type === "tool" && parsed.task_status)
              setPlanSteps((steps) =>
                steps.map((step) => ({
                  ...step,
                  status: parsed.task_status[step.id] ?? step.status,
                })),
              );
            if (type === "error" || parsed.error)
              throw new Error(
                streamErrors[parsed.code] ||
                  parsed.error ||
                  "Luồng phản hồi bị gián đoạn",
              );
          } catch (cause) {
            if (cause instanceof SyntaxError) answer += data;
            else throw cause;
          }
          setMessages((rows) =>
            rows.map((message) =>
              message.id === assistantId
                ? { ...message, content: answer }
                : message,
            ),
          );
        }
      }
      await reload();
      return true;
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") return true;
      setError(
        cause instanceof Error ? cause.message : "Không thể gửi yêu cầu",
      );
      return false;
    } finally {
      if (approvalTimer) clearInterval(approvalTimer);
      requestController.current = null;
      setSending(false);
    }
  };
  const stop = async () => {
    requestController.current?.abort();
    if (sessionId) await cancelAiExecutionAPI(sessionId).catch(() => undefined);
    setSending(false);
    setNotice("Đã dừng tiến trình");
  };
  const resolveApproval = async (
    approvalId: string,
    status: "APPROVED" | "REJECTED",
  ) => {
    try {
      await resolveAiApprovalAPI(approvalId, status);
      setApprovals((rows) =>
        rows.filter((item) => item.intervention_id !== approvalId),
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Không thể gửi lựa chọn xác nhận",
      );
    }
  };
  return {
    user,
    authLoading,
    sessions,
    sessionId,
    messages,
    quota,
    instructions,
    loading,
    sending,
    error,
    notice,
    planSteps,
    openedMode,
    approvals,
    clearNotice: () => setNotice(""),
    reload,
    newChat,
    openSession,
    removeSession,
    renameSession,
    saveInstructions,
    send,
    stop,
    resolveApproval,
  };
}
