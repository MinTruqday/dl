"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/features/authentication/contexts/AuthContext";
import { clearUserInstructionsAPI, cancelAiExecutionAPI, createAiSessionAPI, deleteAiSessionAPI, getAiSessionAPI, getAiSessionsAPI, getAiCapabilitiesAPI, getAiWorkspaceAPI, getPendingAiApprovalsAPI, getUserInstructionsAPI, saveUserInstructionsAPI, resolveAiApprovalAPI, streamAiChatAPI, updateAiSessionTitleAPI, updateAiSessionStateAPI, } from "@/features/ai/services/interaction.service";
import { uploadChatAttachmentAPI } from "@/features/cloud/services/upload.service";
const streamErrors = {
    document_access_denied: "Không có quyền đọc tài liệu",
    document_access_verification_failed: "Không thể xác minh quyền tài liệu",
    input_security_blocked: "Yêu cầu bị chặn bởi chính sách an toàn",
    planning_model_failed: "Không thể lập kế hoạch",
    orchestration_failed: "Không thể thực hiện kế hoạch",
    model_generation_failed: "Mô hình AI không thể tạo câu trả lời",
    response_verification_failed: "Kết quả không vượt qua bước kiểm chứng",
    chat_stream_failed: "Luồng phản hồi bị gián đoạn",
    multimodal_processing_failed: "Không thể xử lý tệp đa phương tiện",
};
function readDataUrl(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ""));
        reader.onerror = () => reject(new Error("Không thể đọc tệp đính kèm"));
        reader.readAsDataURL(file);
    });
}
async function buildFolderData(files) {
    const textExtensions = /\.(txt|md|markdown|json|csv|tsv|xml|html?|css|js|jsx|ts|tsx|py|java|c|cpp|h|hpp|go|rs|rb|php|sql|yaml|yml|toml|ini|tex)$/i;
    const sections = [];
    let totalCharacters = 0;
    for (const file of files.slice(0, 50)) {
        const path = file.webkitRelativePath || file.name;
        if (!file.type.startsWith("text/") && !textExtensions.test(file.name)) {
            sections.push(`--- ${path}\n[Tệp không phải văn bản]`);
            continue;
        }
        const remaining = 1500000 - totalCharacters;
        if (remaining <= 0)
            break;
        const content = (await file.text()).slice(0, Math.min(remaining, 120000));
        totalCharacters += content.length;
        sections.push(`--- ${path}\n${content}`);
    }
    const bytes = new TextEncoder().encode(sections.join("\n\n"));
    let binary = "";
    for (let offset = 0; offset < bytes.length; offset += 0x8000) {
        binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
    }
    return `data:text/plain;base64,${btoa(binary)}`;
}
export function useChat(documentId) {
    const { user, isLoading: authLoading } = useAuth();
    const [sessions, setSessions] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [instructions, setInstructions] = useState("");
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const [planSteps, setPlanSteps] = useState([]);
    const [openedMode, setOpenedMode] = useState(null);
    const [workspace, setWorkspace] = useState({
        objective: "",
        status: "",
        mode: null,
    });
    const [approvals, setApprovals] = useState([]);
    const [activeModel, setActiveModel] = useState("");
    const [audioAvailable, setAudioAvailable] = useState(false);
    const requestController = useRef(null);
    const reload = useCallback(async () => {
        var _a, _b, _c, _d, _e, _f;
        if (!user)
            return setLoading(false);
        setLoading(true);
        try {
            const [sessionResponse, instructionResponse, capabilities] = await Promise.all([
                getAiSessionsAPI(undefined, user._id),
                getUserInstructionsAPI(),
                getAiCapabilitiesAPI().catch(() => ({
                    model: "",
                    audio_input: false,
                })),
            ]);
            setSessions((_b = (_a = sessionResponse.data) !== null && _a !== void 0 ? _a : sessionResponse) !== null && _b !== void 0 ? _b : []);
            setInstructions((_e = (_d = (_c = instructionResponse.data) === null || _c === void 0 ? void 0 : _c.instructions) !== null && _d !== void 0 ? _d : instructionResponse.instructions) !== null && _e !== void 0 ? _e : "");
            setActiveModel(String((_f = capabilities.model) !== null && _f !== void 0 ? _f : ""));
            setAudioAvailable(Boolean(capabilities.audio_input));
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : "Không thể tải trò chuyện");
        }
        finally {
            setLoading(false);
        }
    }, [user]);
    useEffect(() => void reload(), [reload]);
    const newChat = () => {
        setSessionId(null);
        setMessages([]);
        setPlanSteps([]);
        setOpenedMode(null);
        setWorkspace({ objective: "", status: "", mode: null });
        setApprovals([]);
        setError("");
    };
    const openSession = async (id) => {
        var _a, _b, _c, _d, _e, _f, _g, _h, _j;
        setLoading(true);
        setError("");
        try {
            const [response, workspace] = await Promise.all([
                getAiSessionAPI(id),
                getAiWorkspaceAPI(id),
            ]);
            const row = (_a = response.data) !== null && _a !== void 0 ? _a : response;
            setSessionId(id);
            const workspaceMode = ((_c = (_b = workspace === null || workspace === void 0 ? void 0 : workspace.mode) !== null && _b !== void 0 ? _b : row.mode) !== null && _c !== void 0 ? _c : "chat");
            setOpenedMode(workspaceMode);
            setWorkspace({
                objective: String((_e = (_d = workspace === null || workspace === void 0 ? void 0 : workspace.objective) !== null && _d !== void 0 ? _d : row.first_query) !== null && _e !== void 0 ? _e : ""),
                status: String((_f = workspace === null || workspace === void 0 ? void 0 : workspace.status) !== null && _f !== void 0 ? _f : ""),
                mode: workspaceMode,
            });
            setPlanSteps(((_g = workspace === null || workspace === void 0 ? void 0 : workspace.steps) !== null && _g !== void 0 ? _g : []).map((step) => {
                var _a, _b;
                return ({
                    id: String(step.id),
                    task: String((_a = step.task) !== null && _a !== void 0 ? _a : ""),
                    status: (_b = step.status) !== null && _b !== void 0 ? _b : "pending",
                });
            }));
            setMessages(((_j = (_h = row.messages) !== null && _h !== void 0 ? _h : row.history) !== null && _j !== void 0 ? _j : []).map((message) => {
                var _a, _b, _c, _d;
                return ({
                    id: (_b = (_a = message.id) !== null && _a !== void 0 ? _a : message._id) !== null && _b !== void 0 ? _b : crypto.randomUUID(),
                    role: message.role,
                    content: (_d = (_c = message.content) !== null && _c !== void 0 ? _c : message.text) !== null && _d !== void 0 ? _d : "",
                });
            }));
        }
        catch (cause) {
            setError(cause instanceof Error
                ? cause.message
                : "Không thể mở phiên trò chuyện");
        }
        finally {
            setLoading(false);
        }
    };
    const removeSession = async (id) => {
        try {
            await deleteAiSessionAPI(id);
            if (sessionId === id)
                newChat();
            await reload();
        }
        catch (cause) {
            setError(cause instanceof Error
                ? cause.message
                : "Không thể xóa phiên trò chuyện");
        }
    };
    const renameSession = async (id, title) => {
        try {
            await updateAiSessionTitleAPI(id, title.trim());
            await reload();
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : "Không thể đổi tên phiên");
        }
    };
    const setSessionState = async (id, state) => {
        try {
            await updateAiSessionStateAPI(id, state);
            if (state.is_archived && sessionId === id)
                newChat();
            await reload();
        }
        catch (cause) {
            setError(cause instanceof Error
                ? cause.message
                : "Không thể cập nhật cuộc trò chuyện");
        }
    };
    const saveInstructions = async (value) => {
        try {
            if (value.trim())
                await saveUserInstructionsAPI(value.trim());
            else
                await clearUserInstructionsAPI();
            setInstructions(value.trim());
            setNotice("Đã lưu chỉ dẫn cá nhân");
            return true;
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : "Không thể lưu chỉ dẫn");
            return false;
        }
    };
    const send = async (text, mode, approvalPolicy, attachmentSelection, thinkingEnabled = false) => {
        var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m;
        const selectedFiles = (_a = attachmentSelection === null || attachmentSelection === void 0 ? void 0 : attachmentSelection.files) !== null && _a !== void 0 ? _a : [];
        const firstFile = selectedFiles[0];
        if ((!text.trim() && !firstFile) || sending)
            return false;
        setSending(true);
        setError("");
        let activeSession = sessionId;
        let approvalTimer = null;
        let responseTimer = null;
        let pendingAssistantId = "";
        let responseTimedOut = false;
        try {
            const effectiveText = text.trim() ||
                ((attachmentSelection === null || attachmentSelection === void 0 ? void 0 : attachmentSelection.kind) === "folder"
                    ? "Phân tích thư mục đính kèm"
                    : (firstFile === null || firstFile === void 0 ? void 0 : firstFile.type.startsWith("audio/"))
                        ? "Phân tích nội dung âm thanh đính kèm"
                        : (firstFile === null || firstFile === void 0 ? void 0 : firstFile.type.startsWith("image/"))
                            ? "Phân tích nội dung hình ảnh đính kèm"
                            : "Phân tích tệp đính kèm");
            if (!activeSession) {
                const created = await createAiSessionAPI("", effectiveText, mode);
                activeSession = (_c = (_b = created.data) === null || _b === void 0 ? void 0 : _b._id) !== null && _c !== void 0 ? _c : created._id;
                setSessionId(activeSession);
                setOpenedMode(mode);
                setPlanSteps([]);
                setWorkspace({
                    objective: effectiveText,
                    status: mode === "plan" ? "planning" : mode === "chat" ? "" : "running",
                    mode,
                });
            }
            const refreshApprovals = async () => {
                if (!activeSession)
                    return;
                const rows = await getPendingAiApprovalsAPI(activeSession).catch(() => []);
                setApprovals(rows);
            };
            approvalTimer = setInterval(() => void refreshApprovals(), 750);
            void refreshApprovals();
            const attachments = await Promise.all(selectedFiles.slice(0, 50).map(async (file) => {
                var _a;
                const uploaded = await uploadChatAttachmentAPI(file);
                return {
                    url: (_a = uploaded.data) === null || _a === void 0 ? void 0 : _a.url,
                    filename: file.webkitRelativePath ||
                        file.name,
                    content_type: file.type || "application/octet-stream",
                    size: file.size,
                };
            }));
            const multimodalData = firstFile &&
                (firstFile.type.startsWith("image/") || firstFile.type.startsWith("audio/"))
                ? await readDataUrl(firstFile)
                : null;
            const fileData = firstFile && (attachmentSelection === null || attachmentSelection === void 0 ? void 0 : attachmentSelection.kind) === "file" && !multimodalData
                ? await readDataUrl(firstFile)
                : null;
            const folderData = (attachmentSelection === null || attachmentSelection === void 0 ? void 0 : attachmentSelection.kind) === "folder"
                ? await buildFolderData(selectedFiles)
                : null;
            const userMessage = {
                id: crypto.randomUUID(),
                role: "user",
                content: effectiveText,
                attachment: attachments.map((item) => item.filename).join(", ") || undefined,
            };
            const assistantId = crypto.randomUUID();
            pendingAssistantId = assistantId;
            setMessages((rows) => [
                ...rows,
                userMessage,
                { id: assistantId, role: "assistant", content: "", pending: true },
            ]);
            requestController.current = new AbortController();
            responseTimer = setTimeout(() => {
                var _a;
                responseTimedOut = true;
                (_a = requestController.current) === null || _a === void 0 ? void 0 : _a.abort();
            }, 300000);
            const response = await streamAiChatAPI({
                query: effectiveText,
                thinking: thinkingEnabled,
                mode,
                approval_policy: approvalPolicy,
                session_id: activeSession,
                conversation_history: messages.slice(-8),
                user_id: user === null || user === void 0 ? void 0 : user._id,
                document_ids: documentId ? [documentId] : [],
                attachments,
                image_data: (firstFile === null || firstFile === void 0 ? void 0 : firstFile.type.startsWith("image/")) ? multimodalData : null,
                audio_data: (firstFile === null || firstFile === void 0 ? void 0 : firstFile.type.startsWith("audio/")) ? multimodalData : null,
                file_data: fileData,
                folder_data: folderData,
            }, requestController.current.signal);
            if (!response.ok || !response.body) {
                const body = await response.json().catch(() => ({}));
                throw new Error(body.message || body.detail || "Dịch vụ AI không phản hồi");
            }
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let answer = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                buffer += decoder.decode(value, { stream: true });
                const events = buffer.split("\n\n");
                buffer = events.pop() || "";
                for (const event of events) {
                    const lines = event.split("\n");
                    const type = (_d = lines
                        .find((line) => line.startsWith("event:"))) === null || _d === void 0 ? void 0 : _d.slice(6).trim();
                    const data = (_e = lines
                        .find((line) => line.startsWith("data:"))) === null || _e === void 0 ? void 0 : _e.slice(5).trim();
                    if (!data || type === "done" || data === "[DONE]")
                        continue;
                    try {
                        const parsed = JSON.parse(data);
                        if (type === "message" || !type) {
                            answer += (_g = (_f = parsed.chunk) !== null && _f !== void 0 ? _f : parsed.answer) !== null && _g !== void 0 ? _g : "";
                        }
                        if (type === "plan" && Array.isArray(parsed.steps))
                            setPlanSteps(parsed.steps.map((step, index) => {
                                var _a, _b, _c;
                                return ({
                                    id: String((_a = step.id) !== null && _a !== void 0 ? _a : index + 1),
                                    task: String((_b = step.task) !== null && _b !== void 0 ? _b : ""),
                                    status: (_c = step.status) !== null && _c !== void 0 ? _c : "pending",
                                });
                            }));
                        if (type === "tool" && parsed.task_status)
                            setPlanSteps((steps) => steps.map((step) => {
                                var _a;
                                return (Object.assign(Object.assign({}, step), { status: (_a = parsed.task_status[step.id]) !== null && _a !== void 0 ? _a : step.status }));
                            }));
                        if (type === "model") {
                            setActiveModel(String((_h = parsed.model) !== null && _h !== void 0 ? _h : ""));
                            setAudioAvailable(Boolean(parsed.audio_input));
                        }
                        if (type === "error" || parsed.error)
                            throw new Error(streamErrors[parsed.code] ||
                                parsed.error ||
                                "Luồng phản hồi bị gián đoạn");
                    }
                    catch (cause) {
                        if (cause instanceof SyntaxError)
                            answer += data;
                        else
                            throw cause;
                    }
                    if (answer) {
                        setMessages((rows) => {
                            const existing = rows.some((message) => message.id === assistantId);
                            if (!existing)
                                return [...rows, { id: assistantId, role: "assistant", content: answer }];
                            return rows.map((message) => message.id === assistantId
                                ? Object.assign(Object.assign({}, message), { content: answer, pending: false }) : message);
                        });
                    }
                }
            }
            if (!answer) {
                throw new Error("Mô hình AI không trả về nội dung");
            }
            if (activeSession && mode !== "chat") {
                const currentWorkspace = await getAiWorkspaceAPI(activeSession).catch(() => null);
                if (currentWorkspace) {
                    setWorkspace({
                        objective: String((_j = currentWorkspace.objective) !== null && _j !== void 0 ? _j : effectiveText),
                        status: String((_k = currentWorkspace.status) !== null && _k !== void 0 ? _k : ""),
                        mode: ((_l = currentWorkspace.mode) !== null && _l !== void 0 ? _l : mode),
                    });
                    setPlanSteps(((_m = currentWorkspace.steps) !== null && _m !== void 0 ? _m : []).map((step, index) => {
                        var _a, _b, _c, _d;
                        return ({
                            id: String((_a = step.id) !== null && _a !== void 0 ? _a : index + 1),
                            task: String((_c = (_b = step.task) !== null && _b !== void 0 ? _b : step.action) !== null && _c !== void 0 ? _c : ""),
                            status: (_d = step.status) !== null && _d !== void 0 ? _d : "pending",
                        });
                    }));
                }
            }
            await reload();
            return true;
        }
        catch (cause) {
            const message = responseTimedOut
                ? "AI phản hồi quá lâu. Hãy thử lại với câu hỏi ngắn hơn."
                : cause instanceof DOMException && cause.name === "AbortError"
                    ? ""
                    : cause instanceof Error
                        ? cause.message
                        : "Không thể gửi yêu cầu";
            if (message) {
                setMessages((rows) => rows.map((row) => row.id === pendingAssistantId
                    ? Object.assign(Object.assign({}, row), { content: message, pending: false }) : row));
                setError(message);
                return false;
            }
            setMessages((rows) => rows.filter((row) => row.id !== pendingAssistantId));
            return false;
        }
        finally {
            if (approvalTimer)
                clearInterval(approvalTimer);
            if (responseTimer)
                clearTimeout(responseTimer);
            requestController.current = null;
            setSending(false);
        }
    };
    const stop = async () => {
        var _a;
        (_a = requestController.current) === null || _a === void 0 ? void 0 : _a.abort();
        if (sessionId)
            await cancelAiExecutionAPI(sessionId).catch(() => undefined);
        setSending(false);
        setNotice("Đã dừng tiến trình");
    };
    const resolveApproval = async (approvalId, status, scope = "once") => {
        try {
            await resolveAiApprovalAPI(approvalId, status, scope);
            setApprovals((rows) => rows.filter((item) => item.intervention_id !== approvalId));
        }
        catch (cause) {
            setError(cause instanceof Error ? cause.message : "Không thể gửi lựa chọn xác nhận");
        }
    };
    return {
        user,
        authLoading,
        sessions,
        sessionId,
        messages,
        instructions,
        loading,
        sending,
        error,
        notice,
        planSteps,
        openedMode,
        workspace,
        approvals,
        activeModel,
        audioAvailable,
        clearNotice: () => setNotice(""),
        reportError: setError,
        reload,
        newChat,
        openSession,
        removeSession,
        renameSession,
        setSessionState,
        saveInstructions,
        send,
        stop,
        resolveApproval,
    };
}
