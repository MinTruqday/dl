import { API, BlockTool } from "@editorjs/editorjs";
import {
  API_URL,
  getAuthHeaders,
} from "@/shared/services/api-client";

export default class DocLibAiText implements BlockTool {
  static readonly feature = {
    id: "DocLibAiText",
    title: "DocLib AiText",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="38f70a61c87e820c"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="9,13 14,16 17,11 15,16 19,10 12,18"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    prompt: string;
    response: string;
    status: "idle" | "generating" | "done";
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "Trợ lý viết bằng AI",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="38f70a61c87e820c"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="9,13 14,16 17,11 15,16 19,10 12,18"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({
    api,
    data,
    readOnly,
  }: {
    api: API;
    data?: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      prompt: data.prompt || "",
      response: data.response || "",
      status: data.status || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-ai-text-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-ai-text-styles";
      style.innerHTML = `
            .doclib-ai-wrapper { border: 1px solid hsl(var(--border)); border-radius: 12px; background: linear-gradient(180deg, hsl(var(--surface-raised)) 0%, hsl(var(--surface)) 100%); margin: 16px 0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
            .doclib-ai-header { padding: 12px 16px; background: hsl(var(--brand-soft)); border-bottom: 1px solid hsl(var(--brand-soft)); display: flex; align-items: center; gap: 8px; color: #1e3a8a; font-weight: 600; }
            .doclib-ai-icon { color: hsl(var(--brand)); }
            .doclib-ai-prompt { padding: 16px; display: flex; gap: 8px; border-bottom: 1px solid hsl(var(--border)); }
            .doclib-ai-input { flex-grow: 1; border: 1px solid hsl(var(--border)); padding: 8px 12px; border-radius: 6px; outline: none; transition: border 0.2s; font-size: 14px; }
            .doclib-ai-input:focus { border-color: hsl(var(--brand)); }
            .doclib-ai-btn { background: hsl(var(--brand)); color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; transition: background 0.2s; }
            .doclib-ai-btn:hover { background: hsl(var(--brand)); }
            .doclib-ai-btn:disabled { background: hsl(var(--ink-faint)); cursor: not-allowed; }
            .doclib-ai-response { padding: 16px; min-height: 100px; font-size: 15px; line-height: 1.6; color: hsl(var(--ink)); white-space: pre-wrap; outline: none; }
            .doclib-ai-generating { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; color: hsl(var(--ink-faint)); }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const container = document.createElement("div");
    container.classList.add("doclib-ai-wrapper");

    const header = document.createElement("div");
    header.classList.add("doclib-ai-header");
    header.innerHTML = `
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="38f70a61c87e820c"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="9,13 14,16 17,11 15,16 19,10 12,18"/></svg>
          Trợ lý viết DocLib
      `;
    container.appendChild(header);

    if (!this.readOnly && this.data.status !== "done") {
      const promptRow = document.createElement("div");
      promptRow.classList.add("doclib-ai-prompt");

      const input = document.createElement("input");
      input.classList.add("doclib-ai-input");
      input.placeholder = "Mô tả nội dung cần tạo";
      input.value = this.data.prompt;

      const btn = document.createElement("button");
      btn.classList.add("doclib-ai-btn");
      btn.innerText = "Tạo nội dung";

      if (this.data.status === "generating") {
        input.disabled = true;
        btn.disabled = true;
        btn.innerText = "Đang tạo";
      }

      const submit = () => {
        if (!input.value.trim() || this.data.status === "generating") return;
        this.data.prompt = input.value;
        this.data.response = "";
        this.data.status = "generating";
        this.buildUI();

        const apiUrl = `${API_URL}/suy-luan/tao-noi-dung`;
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 185_000);
        fetch(apiUrl, {
          method: "POST",
          headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            prompt: this.data.prompt,
            max_tokens: 160,
            temperature: 0.3,
          }),
        })
          .then(async (res) => {
            const payload = await res.json().catch(() => ({}));
            if (!res.ok) {
              throw new Error(
                payload.detail?.message ||
                  payload.detail ||
                  payload.message ||
                  "Dịch vụ AI từ chối yêu cầu",
              );
            }
            return payload;
          })
          .then((res) => {
            const response = res.data?.result || res.result;
            if (typeof response !== "string" || !response.trim())
              throw new Error("Dịch vụ AI không trả về nội dung hợp lệ");
            this.data.response = response;
            this.data.status = "done";
            this.buildUI();
          })
          .catch((err) => {
            this.data.response = "";
            this.data.status = "idle";
            this.api.notifier.show({
              message:
                (err instanceof DOMException && err.name === "AbortError"
                  ? "Yêu cầu quá thời gian xử lý"
                  : "Không thể tạo nội dung: " +
                    (err instanceof Error ? err.message : "Lỗi không xác định")),
              style: "error",
            });
            this.buildUI();
          })
          .finally(() => window.clearTimeout(timeout));
      };

      btn.addEventListener("click", submit);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") submit();
      });

      promptRow.appendChild(input);
      promptRow.appendChild(btn);
      container.appendChild(promptRow);
    }

    const responseBox = document.createElement("div");
    responseBox.classList.add("doclib-ai-response");
    responseBox.contentEditable = !this.readOnly ? "true" : "false";

    if (this.data.status === "generating") {
      responseBox.classList.add("doclib-ai-generating");
      responseBox.innerText = "AI đang tạo nội dung";
      responseBox.contentEditable = "false";
    } else if (this.data.status === "done") {
      responseBox.innerText = this.data.response;
      responseBox.addEventListener(
        "input",
        () => (this.data.response = responseBox.innerText),
      );
    } else {
      responseBox.style.display = "none";
    }

    container.appendChild(responseBox);
    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
