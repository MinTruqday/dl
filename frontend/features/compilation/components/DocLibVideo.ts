import { API, BlockTool } from "@editorjs/editorjs";
import {
  getProtectedAssetBlobUrlAPI,
  uploadAssetAPI,
} from "@/features/cloud/services/upload.service";

export default class DocLibVideo implements BlockTool {
  static readonly feature = {
    id: "DocLibVideo",
    title: "DocLib Video",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="dd08117e66526aaf"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="4,12 4,11 4,18 8,9 18,5 8,12"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private previewUrl = "";
  private data: { url: string; caption: string };

  static get toolbox() {
    return {
      title: "DocLib Video",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="dd08117e66526aaf"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="4,12 4,11 4,18 8,9 18,5 8,12"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any; config?: any }) {
    this.api = api;
    this.data = {
      url: data.url || "",
      caption: data.caption || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-video-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-video-styles";
      style.innerHTML = `
            .doclib-video-wrapper { text-align: center; }
            .doclib-video-player { max-width: 100%; border-radius: 8px; margin-bottom: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); outline: none; }
            .doclib-video-caption { outline: none; text-align: center; color: hsl(var(--ink-muted)); font-size: 0.9em; padding: 4px; }
            .doclib-video-caption:empty::before { content: 'DocLib Input'; color: hsl(var(--ink-faint)); pointer-events: none; }
            .doclib-video-input-container { display: flex; align-items: center; }
            .doclib-video-input { flex-grow: 1; margin-right: 12px; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-video-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    if (this.data.url) {
      const video = document.createElement("video");
      void this.loadPreview(video, this.data.url);
      video.controls = true;
      video.classList.add("doclib-video-player");

      const caption = document.createElement("div");
      caption.contentEditable = "true";
      caption.innerHTML = this.data.caption;
      caption.classList.add("doclib-video-caption");

      caption.addEventListener("input", () => {
        this.data.caption = caption.innerHTML;
      });

      this.wrapper.appendChild(video);
      this.wrapper.appendChild(caption);
    } else {
      const uploader = document.createElement("label");
      uploader.style.display = "flex";
      uploader.style.flexDirection = "column";
      uploader.style.alignItems = "center";
      uploader.style.justifyContent = "center";
      uploader.style.border = "2px dashed hsl(var(--border))";
      uploader.style.borderRadius = "12px";
      uploader.style.padding = "32px";
      uploader.style.background = "hsl(var(--surface-raised))";
      uploader.style.cursor = "pointer";
      uploader.style.color = "hsl(var(--ink-muted))";
      uploader.innerHTML = `
              <div style="color: hsl(var(--ink-faint)); margin-bottom: 12px;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="dd08117e66526aaf"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="4,12 4,11 4,18 8,9 18,5 8,12"/></svg></div>
              <div style="font-weight: 500; font-size: 1.1em; margin-bottom: 4px;">Upload Video</div>
              <div style="font-size: 0.9em; opacity: 0.8;">Click to select file or Right click to paste URL</div>
          `;

      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = "video/*";
      fileInput.style.display = "none";

      fileInput.addEventListener("change", async () => {
        if (fileInput.files && fileInput.files[0]) {
          const file = fileInput.files[0];
          uploader.innerHTML =
            '<div style="padding: 20px; font-weight: 500;">Đang tải lên</div>';
          try {
            const response = await uploadAssetAPI(file, "video");
            this.data.url = response.data.url;
            this.buildUI();
          } catch (reason) {
            uploader.textContent =
              reason instanceof Error ? reason.message : "Không thể tải video";
          }
        }
      });

      uploader.appendChild(fileInput);

      uploader.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        const url = prompt("Enter a direct video URL");
        if (url) {
          this.data.url = url;

          this.buildUI();
        }
      });
      this.wrapper.appendChild(uploader);
    }
  }

  save() {
    return this.data;
  }

  destroy() {
    this.releasePreview();
  }

  private async loadPreview(element: HTMLVideoElement, path: string) {
    try {
      this.releasePreview();
      this.previewUrl = await getProtectedAssetBlobUrlAPI(path);
      element.src = this.previewUrl;
    } catch {
      element.textContent = "Không thể tải video";
    }
  }

  private releasePreview() {
    if (this.previewUrl.startsWith("blob:"))
      URL.revokeObjectURL(this.previewUrl);
    this.previewUrl = "";
  }
}
