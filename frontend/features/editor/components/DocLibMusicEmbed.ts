import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibMusicEmbed implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string; title: string; platform: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Music Embed",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      url: data?.url || "",
      title: data?.title || "",
      platform: data?.platform || "",
    };
  }

  private detectPlatform(url: string): { platform: string; embedUrl: string } | null {
    if (!url) return null;

    const spotifyTrack = url.match(/spotify\.com\/track\/([a-zA-Z0-9]+)/);
    if (spotifyTrack) return { platform: "Spotify", embedUrl: `https://open.spotify.com/embed/track/${spotifyTrack[1]}?utm_source=generator` };

    const spotifyPlaylist = url.match(/spotify\.com\/playlist\/([a-zA-Z0-9]+)/);
    if (spotifyPlaylist) return { platform: "Spotify", embedUrl: `https://open.spotify.com/embed/playlist/${spotifyPlaylist[1]}?utm_source=generator` };

    const spotifyAlbum = url.match(/spotify\.com\/album\/([a-zA-Z0-9]+)/);
    if (spotifyAlbum) return { platform: "Spotify", embedUrl: `https://open.spotify.com/embed/album/${spotifyAlbum[1]}?utm_source=generator` };

    const soundcloud = url.match(/soundcloud\.com\//);
    if (soundcloud) return { platform: "SoundCloud", embedUrl: `https://w.soundcloud.com/player/?url=${encodeURIComponent(url)}&color=%230284c7&auto_play=false&show_artwork=true` };

    const youtube = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/);
    if (youtube) return { platform: "YouTube Music", embedUrl: `https://www.youtube.com/embed/${youtube[1]}` };

    return null;
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-music-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-music-styles";
      style.innerHTML = `
        .doclib-music-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin: 12px 0; }
        .doclib-music-input-area { padding: 16px 20px; background: #f8fafc; display: flex; gap: 8px; }
        .doclib-music-url-input { flex: 1; padding: 9px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px; outline: none; }
        .doclib-music-embed-btn { padding: 9px 16px; background: #0f172a; color: #fff; border: none; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; white-space: nowrap; }
        .doclib-music-hint { padding: 0 20px 12px; font-size: 11px; color: #94a3b8; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
        .doclib-music-iframe { width: 100%; border: none; display: block; }
        .doclib-music-placeholder { padding: 40px; text-align: center; color: #94a3b8; font-size: 14px; }
        .doclib-music-platform-badge { padding: 6px 16px; font-size: 11px; font-weight: 600; color: #64748b; background: #f8fafc; border-top: 1px solid #e2e8f0; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-music-wrapper");

    const detected = this.detectPlatform(this.data.url);

    if (!this.readOnly) {
      const inputArea = document.createElement("div");
      inputArea.classList.add("doclib-music-input-area");

      const urlInput = document.createElement("input");
      urlInput.classList.add("doclib-music-url-input");
      urlInput.value = this.data.url;
      urlInput.placeholder = "Paste Spotify / SoundCloud / YouTube link";

      const embedBtn = document.createElement("button");
      embedBtn.classList.add("doclib-music-embed-btn");
      embedBtn.innerText = "Embed";

      embedBtn.addEventListener("click", () => {
        this.data.url = urlInput.value.trim();
        this.buildUI();
      });

      urlInput.addEventListener("keydown", (e) => { if (e.key === "Enter") embedBtn.click(); });

      inputArea.appendChild(urlInput);
      inputArea.appendChild(embedBtn);
      this.wrapper.appendChild(inputArea);

      const hint = document.createElement("div");
      hint.classList.add("doclib-music-hint");
      hint.innerText = "Support: Spotify (track/playlist/album)  SoundCloud  YouTube";
      this.wrapper.appendChild(hint);
    }

    if (detected) {
      const iframeHeight = detected.platform === "Spotify" ? "152" : detected.platform === "SoundCloud" ? "166" : "315";
      const iframe = document.createElement("iframe");
      iframe.classList.add("doclib-music-iframe");
      iframe.height = iframeHeight;
      iframe.src = detected.embedUrl;
      iframe.allowFullscreen = true;
      iframe.allow = "autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture";

      const badge = document.createElement("div");
      badge.classList.add("doclib-music-platform-badge");
      badge.innerText = ` ${detected.platform}`;

      this.wrapper.appendChild(iframe);
      this.wrapper.appendChild(badge);
    } else if (!this.readOnly) {
      const placeholder = document.createElement("div");
      placeholder.classList.add("doclib-music-placeholder");
      placeholder.innerText = " Paste a music link to embed";
      this.wrapper.appendChild(placeholder);
    }
  }

  save() {
    return this.data;
  }
}
