"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import {
  clearUserInstructionsAPI,
  createAiSessionAPI,
  deleteAiSessionAPI,
  getAiSessionAPI,
  getAiSessionsAPI,
  getUserInstructionsAPI,
  saveUserInstructionsAPI,
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
    setError("");
  };
  const openSession = async (id: string) => {
    setLoading(true);
    setError("");
    try {
      const response = await getAiSessionAPI(id);
      const row = response.data ?? response;
      setSessionId(id);
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
  const send = async (text: string, thinking: boolean, file?: File | null) => {
    if ((!text.trim() && !file) || sending) return false;
    setSending(true);
    setError("");
    let activeSession = sessionId;
    try {
      if (!activeSession) {
        const created = await createAiSessionAPI("", text.trim());
        activeSession = created.data?._id ?? created._id;
        setSessionId(activeSession);
      }
      let attachment: any = null;
      if (file) {
        const uploaded = await uploadChatAttachmentAPI(file);
        attachment = { url: uploaded.data?.url, filename: file.name };
      }
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text.trim(),
        attachment: file?.name,
      };
      const assistantId = crypto.randomUUID();
      setMessages((rows) => [
        ...rows,
        userMessage,
        { id: assistantId, role: "assistant", content: "" },
      ]);
      const response = await streamAiChatAPI({
        query: text.trim(),
        thinking,
        session_id: activeSession,
        conversation_history: messages.slice(-8),
        user_id: user?._id,
        document_ids: documentId ? [documentId] : [],
        attachments: attachment ? [attachment] : [],
      });
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
            if (type === "error" || parsed.error)
              throw new Error(parsed.error || "Luồng phản hồi bị gián đoạn");
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
      setError(
        cause instanceof Error ? cause.message : "Không thể gửi yêu cầu",
      );
      return false;
    } finally {
      setSending(false);
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
    clearNotice: () => setNotice(""),
    reload,
    newChat,
    openSession,
    removeSession,
    renameSession,
    saveInstructions,
    send,
  };
}
