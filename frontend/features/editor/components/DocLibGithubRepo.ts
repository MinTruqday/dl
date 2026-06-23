import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibGithubRepo implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Github Repo",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      repoUrl: data?.repoUrl || "",
      repoName: data?.repoName || "",
      desc: data?.desc || "",
      stars: data?.stars || "0",
      forks: data?.forks || "0",
      language: data?.language || "TypeScript",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-gh { border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; background: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; max-width: 450px; margin: 16px auto; }
      .doclib-gh-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
      .doclib-gh-icon { color: #64748b; }
      .doclib-gh-name { font-size: 16px; font-weight: 600; color: #0969da; text-decoration: none; outline: none; }
      .doclib-gh-name:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-gh-desc { font-size: 12px; color: #57606a; margin-bottom: 16px; outline: none; line-height: 1.5; }
      .doclib-gh-desc:empty:before { content: attr(data-placeholder); color: #94a3b8; }
      .doclib-gh-stats { display: flex; align-items: center; gap: 16px; font-size: 12px; color: #57606a; }
      .doclib-gh-stat { display: flex; align-items: center; gap: 4px; outline: none; }
      .doclib-gh-stat:empty:before { content: "0"; color: #94a3b8; }
      .doclib-gh-lang-color { width: 12px; height: 12px; border-radius: 50%; background: #3178c6; }
      .doclib-gh-input { width: 100%; padding: 8px; margin-bottom: 12px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px; }
    `;
    this.wrapper.appendChild(style);

    const card = document.createElement("div");
    card.classList.add("doclib-gh");

    if (!this.readOnly) {
      const urlInput = document.createElement("input");
      urlInput.classList.add("doclib-gh-input");
      urlInput.placeholder = "DocLib Github Repo URL";
      urlInput.value = this.data.repoUrl;
      urlInput.addEventListener("input", () => {
        this.data.repoUrl = urlInput.value;
      });
      card.appendChild(urlInput);
    }

    const header = document.createElement("div");
    header.classList.add("doclib-gh-header");
    
    const icon = document.createElement("div");
    icon.classList.add("doclib-gh-icon");
    icon.innerHTML = '<svg height="16" viewBox="0 0 16 16" version="1.1" width="16" aria-hidden="true" fill="currentColor"><path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1v7.5h-8a2.5 2.5 0 0 1-2.5-2.5v-4a2.5 2.5 0 0 1 2.5-2.5Z"></path></svg>';

    const nameEl = document.createElement("a");
    nameEl.classList.add("doclib-gh-name");
    nameEl.innerText = this.data.repoName;
    nameEl.dataset.placeholder = "DocLib Repo Name";
    if (this.readOnly && this.data.repoUrl) {
      nameEl.href = this.data.repoUrl;
      nameEl.target = "_blank";
    }
    if (!this.readOnly) {
      nameEl.contentEditable = "true";
      nameEl.addEventListener("input", () => { this.data.repoName = nameEl.innerText; });
    }

    header.appendChild(icon);
    header.appendChild(nameEl);
    card.appendChild(header);

    const descEl = document.createElement("div");
    descEl.classList.add("doclib-gh-desc");
    descEl.innerText = this.data.desc;
    descEl.dataset.placeholder = "DocLib Repo Description";
    if (!this.readOnly) {
      descEl.contentEditable = "true";
      descEl.addEventListener("input", () => { this.data.desc = descEl.innerText; });
    }
    card.appendChild(descEl);

    const stats = document.createElement("div");
    stats.classList.add("doclib-gh-stats");

    const langWrap = document.createElement("div");
    langWrap.style.display = "flex";
    langWrap.style.alignItems = "center";
    langWrap.style.gap = "4px";
    const langColor = document.createElement("div");
    langColor.classList.add("doclib-gh-lang-color");
    const langEl = document.createElement("div");
    langEl.classList.add("doclib-gh-stat");
    langEl.innerText = this.data.language;
    langEl.dataset.placeholder = "Language";
    if (!this.readOnly) {
      langEl.contentEditable = "true";
      langEl.addEventListener("input", () => { this.data.language = langEl.innerText; });
    }
    langWrap.appendChild(langColor);
    langWrap.appendChild(langEl);
    stats.appendChild(langWrap);

    const starWrap = document.createElement("div");
    starWrap.style.display = "flex";
    starWrap.style.alignItems = "center";
    starWrap.style.gap = "4px";
    starWrap.innerHTML = '<svg height="16" viewBox="0 0 16 16" width="16" fill="currentColor"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"></path></svg>';
    const starEl = document.createElement("div");
    starEl.classList.add("doclib-gh-stat");
    starEl.innerText = this.data.stars;
    starEl.dataset.placeholder = "0";
    if (!this.readOnly) {
      starEl.contentEditable = "true";
      starEl.addEventListener("input", () => { this.data.stars = starEl.innerText; });
    }
    starWrap.appendChild(starEl);
    stats.appendChild(starWrap);

    const forkWrap = document.createElement("div");
    forkWrap.style.display = "flex";
    forkWrap.style.alignItems = "center";
    forkWrap.style.gap = "4px";
    forkWrap.innerHTML = '<svg height="16" viewBox="0 0 16 16" width="16" fill="currentColor"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"></path></svg>';
    const forkEl = document.createElement("div");
    forkEl.classList.add("doclib-gh-stat");
    forkEl.innerText = this.data.forks;
    forkEl.dataset.placeholder = "0";
    if (!this.readOnly) {
      forkEl.contentEditable = "true";
      forkEl.addEventListener("input", () => { this.data.forks = forkEl.innerText; });
    }
    forkWrap.appendChild(forkEl);
    stats.appendChild(forkWrap);

    card.appendChild(stats);
    this.wrapper.appendChild(card);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
