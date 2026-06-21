import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibAudio implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private config: any;
  private data: { url: string; caption: string };

  static get toolbox() {
    return {
      title: "DocLib Audio",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, config }: { api: API; data: any }) {
    this.api = api;
    this.config = config || {};
    this.data = {
      url: data.url || "",
      caption: data.caption || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-audio-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-audio-styles";
      style.innerHTML = `
            .doclib-audio-wrapper { text-align: center; }
            .doclib-audio-player { width: 100%; border-radius: 8px; margin-bottom: 8px; outline: none; }
            .doclib-audio-caption { outline: none; text-align: center; color: #64748b; font-size: 0.9em; padding: 4px; }
            .doclib-audio-caption:empty::before { content: 'DocLib Input'; color: #94a3b8; pointer-events: none; }
            .doclib-audio-input-container { display: flex; align-items: center; }
            .doclib-audio-input { flex-grow: 1; margin-right: 12px; }
        `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-audio-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    if (this.data.url) {
      const audio = document.createElement("audio");
      audio.src = this.data.url;
      audio.controls = true;
      audio.classList.add("doclib-audio-player");

      const caption = document.createElement("div");
      caption.contentEditable = "true";
      caption.innerHTML = this.data.caption;
      caption.classList.add("doclib-audio-caption");

      caption.addEventListener("input", () => {
        this.data.caption = caption.innerHTML;
      });

      this.wrapper.appendChild(audio);
      this.wrapper.appendChild(caption);
    } else {
      const uploader = document.createElement("label");
      uploader.style.display = "flex";
      uploader.style.flexDirection = "column";
      uploader.style.alignItems = "center";
      uploader.style.justifyContent = "center";
      uploader.style.border = "2px dashed #cbd5e1";
      uploader.style.borderRadius = "12px";
      uploader.style.padding = "32px";
      uploader.style.background = "#f8fafc";
      uploader.style.cursor = "pointer";
      uploader.style.color = "#475569";
      uploader.innerHTML = `
              <div style="color: #94a3b8; margin-bottom: 12px;"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg></div>
              <div style="font-weight: 500; font-size: 1.1em; margin-bottom: 4px;">Upload Audio</div>
              <div style="font-size: 0.9em; opacity: 0.8;">Click to select file or Right click to paste URL</div>
          `;

      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.style.display = "none";

      fileInput.addEventListener("change", () => {
        if (fileInput.files && fileInput.files[0]) {
          const file = fileInput.files[0];
          const formData = new FormData();
          formData.append("file", file);
          const endpoint = this.config?.endpoints?.byFile || "/api/uploadFile";

          uploader.innerHTML =
            '<div style="padding: 20px; font-weight: 500;">Uploading...</div>';

          fetch(endpoint, { method: "POST", body: formData })
            .then((res) => res.json())
            .then((res) => {
              if (res.success === 1 && res.file && res.file.url) {
                this.data.url = res.file.url;
              } else {
                this.data.url =
                  res.url || res.data?.url || URL.createObjectURL(file);
              }
              this.buildUI();
            })
            .catch((err) => {
              console.error("Upload failed", err);
              this.data.url = URL.createObjectURL(file);

              this.buildUI();
            });
        }
      });

      uploader.appendChild(fileInput);

      uploader.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        const url = prompt("Paste direct URL:");
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
}
