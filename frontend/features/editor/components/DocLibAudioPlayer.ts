import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibAudioPlayer implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    audioUrl: string;
    coverUrl: string;
    title: string;
    artist: string;
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Audio Player",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>',
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
      audioUrl: data.audioUrl || "",
      coverUrl: data.coverUrl || "",
      title: data.title || "",
      artist: data.artist || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-audio-player-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-audio-player-styles";
      style.innerHTML = `
            .doclib-ap-wrapper { border: 1px solid #e2e8f0; border-radius: 12px; background: #fff; padding: 16px; margin: 16px 0; display: flex; align-items: center; gap: 16px; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1); }
            .doclib-ap-cover { width: 80px; height: 80px; border-radius: 8px; object-fit: cover; background: #f1f5f9; cursor: pointer; flex-shrink: 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
            .doclib-ap-info { flex-grow: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
            .doclib-ap-title { font-weight: 700; font-size: 1.1em; color: #0f172a; outline: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .doclib-ap-title:empty::before { content: 'DocLib Title'; color: #94a3b8; pointer-events: none; }
            .doclib-ap-artist { font-size: 0.9em; color: #64748b; outline: none; }
            .doclib-ap-artist:empty::before { content: 'DocLib Name'; color: #94a3b8; pointer-events: none; }
            .doclib-ap-controls { display: flex; flex-direction: column; gap: 8px; width: 100%; margin-top: 8px; }
            .doclib-ap-audio { width: 100%; height: 32px; }
            .doclib-ap-inputs { display: flex; flex-direction: column; gap: 8px; width: 100%; }
            .doclib-ap-edit-btn { position: absolute; right: 16px; top: 16px; background: transparent; border: none; color: #94a3b8; cursor: pointer; }
            .doclib-ap-edit-btn:hover { color: #0f172a; }
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
    container.classList.add("doclib-ap-wrapper");
    container.style.position = "relative";

    if (this.data.audioUrl) {
      const cover = document.createElement("img");
      cover.classList.add("doclib-ap-cover");
      cover.src =
        this.data.coverUrl ||
        "https://ui-avatars.com/api/?name=Audio&background=f1f5f9&color=94a3b8&size=160";
      cover.addEventListener("click", () => {
        if (this.readOnly) return;
        const url = prompt("Enter Cover Art URL:", this.data.coverUrl);
        if (url !== null) {
          this.data.coverUrl = url;
          this.buildUI();
        }
      });

      const info = document.createElement("div");
      info.classList.add("doclib-ap-info");

      const title = document.createElement("div");
      title.classList.add("doclib-ap-title");
      title.contentEditable = "true";
      title.innerHTML = this.data.title;
      title.addEventListener(
        "input",
        () => (this.data.title = title.innerHTML),
      );

      const artist = document.createElement("div");
      artist.classList.add("doclib-ap-artist");
      artist.contentEditable = "true";
      artist.innerHTML = this.data.artist;
      artist.addEventListener(
        "input",
        () => (this.data.artist = artist.innerHTML),
      );

      const controls = document.createElement("div");
      controls.classList.add("doclib-ap-controls");

      const audio = document.createElement("audio");
      audio.classList.add("doclib-ap-audio");
      audio.controls = true;
      audio.src = this.data.audioUrl;

      controls.appendChild(audio);

      info.appendChild(title);
      info.appendChild(artist);
      info.appendChild(controls);

      container.appendChild(cover);
      container.appendChild(info);

      if (!this.readOnly) {
        const editBtn = document.createElement("button");
        editBtn.classList.add("doclib-ap-edit-btn");
        editBtn.innerHTML =
          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>';
        editBtn.addEventListener("click", () => {
          this.data.audioUrl = "";
          this.buildUI();
        });
        container.appendChild(editBtn);
      }
    } else {
      const inputs = document.createElement("div");
      inputs.classList.add("doclib-ap-inputs");

      const audioInput = document.createElement("input");
      audioInput.classList.add(this.api.styles.input);
      audioInput.placeholder = "DocLib URL";
      audioInput.value = this.data.audioUrl;

      const btn = document.createElement("button");
      btn.classList.add(this.api.styles.button);
      btn.innerText = "Create Audio Player";

      const insert = () => {
        if (audioInput.value) {
          this.data.audioUrl = audioInput.value;
          this.buildUI();
        }
      };

      btn.addEventListener("click", insert);
      audioInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") insert();
      });

      inputs.appendChild(audioInput);
      inputs.appendChild(btn);
      container.appendChild(inputs);
    }

    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
