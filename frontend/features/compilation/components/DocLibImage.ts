import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibImage implements BlockTool {
  static readonly feature = {
    id: "DocLibImage",
    title: "DocLib Image",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6c43fb870f979be0"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,20 17,20 19,19 6,7 8,14 8,11"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private config: any;
  private data: {
    file: { url: string };
    caption: string;
    withBorder: boolean;
    withBackground: boolean;
    stretched: boolean;
  };

  static get toolbox() {
    return {
      title: "DocLib Image",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6c43fb870f979be0"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,20 17,20 19,19 6,7 8,14 8,11"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, config }: { api: API; data: any; config?: any }) {
    this.api = api;
    this.config = config || {};
    this.data = {
      file: { url: data.file?.url || data.url || "" },
      caption: data.caption || "",
      withBorder: data.withBorder || false,
      withBackground: data.withBackground || false,
      stretched: data.stretched || false,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-image-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-image-styles";
      style.innerHTML = `
            .doclib-image-wrapper { text-align: center; margin: 16px 0; }
            .doclib-image-container { position: relative; border-radius: 8px; overflow: hidden; display: inline-block; max-width: 100%; transition: all 0.3s; line-height: 0; }
            .doclib-image-img { max-width: 100%; display: block; border-radius: inherit; }
            .doclib-image-caption { outline: none; text-align: center; color: #64748b; font-size: 0.9em; padding: 8px 4px 4px 4px; }
            .doclib-image-caption:empty::before { content: 'DocLib Input'; color: #94a3b8; pointer-events: none; }
            .doclib-image-container.with-border { border: 2px solid #e2e8f0; }
            .doclib-image-container.with-background { padding: 24px; background: #f1f5f9; border-radius: 12px; }
            .doclib-image-container.stretched { width: 100%; display: block; }
            .doclib-image-container.stretched .doclib-image-img { width: 100%; }
            .doclib-image-uploader { display: flex; flex-direction: column; align-items: center; justify-content: center; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 48px; background: #f8fafc; cursor: pointer; transition: all 0.2s; color: #475569; }
            .doclib-image-uploader:hover { background: #f1f5f9; border-color: #94a3b8; }
            .doclib-image-uploader input[type="file"] { display: none; }
            .doclib-image-icon { color: #94a3b8; margin-bottom: 12px; transition: color 0.2s; }
            .doclib-image-uploader:hover .doclib-image-icon { color: #64748b; }
        `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  renderSettings() {
    const wrapper = document.createElement("div");

    const tunes = [
      {
        name: "withBorder",
        icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6c43fb870f979be0"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,20 17,20 19,19 6,7 8,14 8,11"/></svg>',
      },
      {
        name: "withBackground",
        icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6c43fb870f979be0"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,20 17,20 19,19 6,7 8,14 8,11"/></svg>',
      },
      {
        name: "stretched",
        icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6c43fb870f979be0"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,20 17,20 19,19 6,7 8,14 8,11"/></svg>',
      },
    ];

    tunes.forEach((tune) => {
      const btn = document.createElement("div");
      btn.classList.add(this.api.styles.settingsButton);
      btn.innerHTML = tune.icon;
      if (this.data[tune.name as keyof typeof this.data]) {
        btn.classList.add(this.api.styles.settingsButtonActive);
      }
      btn.addEventListener("click", () => {
        (this.data as any)[tune.name] = !(this.data as any)[tune.name];
        btn.classList.toggle(this.api.styles.settingsButtonActive);
        this.buildUI();
      });
      wrapper.appendChild(btn);
    });

    return wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const outer = document.createElement("div");
    outer.classList.add("doclib-image-wrapper");

    if (this.data.file?.url) {
      const container = document.createElement("div");
      container.classList.add("doclib-image-container");
      if (this.data.withBorder) container.classList.add("with-border");
      if (this.data.withBackground) container.classList.add("with-background");
      if (this.data.stretched) container.classList.add("stretched");

      const img = document.createElement("img");
      img.classList.add("doclib-image-img");
      img.src = this.data.file?.url;

      const caption = document.createElement("div");
      caption.classList.add("doclib-image-caption");
      caption.contentEditable = "true";
      caption.innerHTML = this.data.caption;
      caption.addEventListener(
        "input",
        () => (this.data.caption = caption.innerHTML),
      );

      container.appendChild(img);
      outer.appendChild(container);
      outer.appendChild(caption);
    } else {
      const uploader = document.createElement("label");
      uploader.classList.add("doclib-image-uploader");
      uploader.innerHTML = `
              <div class="doclib-image-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6c43fb870f979be0"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,20 17,20 19,19 6,7 8,14 8,11"/></svg></div>
              <div style="font-weight: 500; font-size: 1.1em; margin-bottom: 4px;">Upload Image</div>
              <div style="font-size: 0.9em; opacity: 0.8;">Click to select file or Right click to paste URL</div>
          `;

      const input = document.createElement("input");
      input.type = "file";
      input.accept = "image/*";
      input.addEventListener("change", () => {
        if (input.files && input.files[0]) {
          const file = input.files[0];
          const formData = new FormData();
          formData.append("file", file);

          const endpoint = this.config.endpoints?.byFile || "/api/uploadFile";

          uploader.innerHTML =
      '<div style="padding: 20px; font-weight: 500;">Uploading</div>';

          fetch(endpoint, {
            method: "POST",
            body: formData,
          })
            .then((res) => res.json())
            .then((res) => {
              if (res.success === 1 && res.file && res.file.url) {
                if (this.data.file) this.data.file.url = res.file.url;
              } else {
                if (this.data.file)
                  this.data.file.url =
                    res.url || res.data?.url || URL.createObjectURL(file);
              }
              this.buildUI();
            })
            .catch((err) => {
              console.error("Image upload failed", err);
              if (this.data.file)
                this.data.file.url = URL.createObjectURL(file);
              this.buildUI();
            });
        }
      });

      uploader.appendChild(input);
      outer.appendChild(uploader);

      uploader.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        const url = prompt("Enter a direct image URL");
        if (url) {
          if (this.data.file) this.data.file.url = url;
          this.buildUI();
        }
      });
    }

    this.wrapper.appendChild(outer);
  }

  save() {
    return this.data;
  }
}
