import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibFile implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private config: any;
  private data: {
    file: { url: string; name: string; size: number; extension: string };
    title: string;
  };

  static get toolbox() {
    return {
      title: "DocLib File Attachment",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, config }: { api: API; data: any }) {
    this.api = api;
    this.config = config || {};
    this.data = {
      file: {
        url: data?.file?.url || "",
        name: data?.file?.name || "",
        size: data?.file?.size || 0,
        extension: data?.file?.extension || "",
      },
      title: data?.title || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-file-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-file-styles";
      style.innerHTML = `
        .doclib-file-card { display: flex; align-items: center; padding: 12px 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; margin: 12px 0; text-decoration: none; color: inherit; }
        .doclib-file-icon { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: #e0f2fe; color: #0284c7; border-radius: 8px; margin-right: 16px; font-weight: bold; font-size: 12px; text-transform: uppercase; }
        .doclib-file-info { flex-grow: 1; display: flex; flex-direction: column; gap: 4px; }
        .doclib-file-title { font-weight: 600; font-size: 1em; outline: none; }
        .doclib-file-title:empty::before { content: 'Enter attachment name'; color: #94a3b8; pointer-events: none; }
        .doclib-file-meta { font-size: 0.85em; color: #64748b; }
        .doclib-file-download { color: #0284c7; cursor: pointer; padding: 8px; }
        .doclib-file-input-container { display: flex; align-items: center; gap: 8px; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    if (this.data?.file?.url) {
      const card = document.createElement("div");
      card.classList.add("doclib-file-card");

      const icon = document.createElement("div");
      icon.classList.add("doclib-file-icon");
      icon.innerText = this.data.file.extension || "FILE";

      const info = document.createElement("div");
      info.classList.add("doclib-file-info");

      const title = document.createElement("div");
      title.classList.add("doclib-file-title");
      title.contentEditable = "true";
      title.innerHTML = this.data.title || this.data.file.name;
      title.addEventListener(
        "input",
        () => (this.data.title = title.innerHTML),
      );

      const meta = document.createElement("div");
      meta.classList.add("doclib-file-meta");
      const sizeMB = this.data.file.size
        ? (this.data.file.size / 1024 / 1024).toFixed(2) + " MB"
        : "";
      meta.innerText = `${this.data.file.name} ${sizeMB ? "• " + sizeMB : ""}`;

      info.appendChild(title);
      info.appendChild(meta);

      const download = document.createElement("a");
      download.classList.add("doclib-file-download");
      download.href = this.data?.file?.url;
      download.target = "_blank";
      download.innerHTML =
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>';

      card.appendChild(icon);
      card.appendChild(info);
      card.appendChild(download);
      this.wrapper.appendChild(card);
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
              <div style="color: #94a3b8; margin-bottom: 12px;"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg></div>
              <div style="font-weight: 500; font-size: 1.1em; margin-bottom: 4px;">Upload Attachment</div>
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
                this.data.file = {
                  url: res.file.url,
                  name: file.name,
                  size: file.size,
                  extension: file.name.split(".").pop().toUpperCase(),
                };
                this.data.title = file.name;
              } else {
                this.data.url =
                  res.url || res.data?.url || URL.createObjectURL(file);
                this.data.file = {
                  url: this.data.url,
                  name: file.name,
                  size: file.size,
                  extension: file.name.split(".").pop().toUpperCase(),
                };
                this.data.title = file.name;
              }
              this.buildUI();
            })
            .catch((err) => {
              console.error("Upload failed", err);
              this.data.url = URL.createObjectURL(file);
              this.data.file = {
                url: this.data.url,
                name: file.name,
                size: file.size,
                extension: file.name.split(".").pop().toUpperCase(),
              };
              this.data.title = file.name;
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
          this.data.file = {
            url,
            name: url.split("/").pop(),
            size: 0,
            extension: "FILE",
          };
          this.data.title = url.split("/").pop();
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
