import { API, BlockTool } from "@editorjs/editorjs";

type SocialPlatform = "twitter" | "linkedin" | "github";

export default class DocLibSocialCard implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    platform: SocialPlatform;
    username: string;
    displayName: string;
    bio: string;
    avatar: string;
    followers: string;
    url: string;
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Social Card",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      platform: data?.platform || "github",
      username: data?.username || "username",
      displayName: data?.displayName || "Display name",
      bio: data?.bio || "Short bio",
      avatar: data?.avatar || "",
      followers: data?.followers || "0",
      url: data?.url || "",
    };
  }

  private getPlatformConfig(platform: SocialPlatform) {
    const map = {
      github: { color: "#24292e", label: "GitHub", icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/></svg>' },
      twitter: { color: "#1DA1F2", label: "Twitter / X", icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>' },
      linkedin: { color: "#0077B5", label: "LinkedIn", icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>' },
    };
    return map[platform];
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-sc-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-sc-styles";
      style.innerHTML = `
        .doclib-sc-wrapper { border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; margin: 12px 0; max-width: 400px; }
        .doclib-sc-header { height: 80px; }
        .doclib-sc-body { padding: 16px 20px 20px; background: #fff; }
        .doclib-sc-avatar-row { display: flex; align-items: flex-end; justify-content: space-between; margin-top: -36px; margin-bottom: 12px; }
        .doclib-sc-avatar { width: 72px; height: 72px; border-radius: 50%; border: 3px solid #fff; background: #e2e8f0; overflow: hidden; display: flex; align-items: center; justify-content: center; font-size: 28px; }
        .doclib-sc-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .doclib-sc-platform-badge { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; color: #fff; }
        .doclib-sc-display-name { font-size: 18px; font-weight: 700; color: #0f172a; }
        .doclib-sc-username { font-size: 13px; color: #64748b; margin-top: 2px; }
        .doclib-sc-bio { font-size: 13px; color: #475569; margin-top: 10px; line-height: 1.5; }
        .doclib-sc-stats { display: flex; gap: 20px; margin-top: 14px; padding-top: 14px; border-top: 1px solid #f1f5f9; }
        .doclib-sc-stat { display: flex; flex-direction: column; }
        .doclib-sc-stat-num { font-size: 15px; font-weight: 700; color: #0f172a; }
        .doclib-sc-stat-label { font-size: 11px; color: #94a3b8; }
        .doclib-sc-edit { border-top: 1px solid #e2e8f0; padding: 16px 20px; background: #f8fafc; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .doclib-sc-edit-field { display: flex; flex-direction: column; gap: 3px; }
        .doclib-sc-edit-field label { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; }
        .doclib-sc-edit-field input { padding: 7px 9px; border: 1px solid #e2e8f0; border-radius: 5px; font-size: 12px; outline: none; }
        .doclib-sc-platform-row { grid-column: 1 / -1; display: flex; gap: 8px; }
        .doclib-sc-platform-btn { flex: 1; padding: 6px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer; background: #fff; }
        .doclib-sc-platform-btn.active { color: #fff; border-color: transparent; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-sc-wrapper");

    const cfg = this.getPlatformConfig(this.data.platform);

    const header = document.createElement("div");
    header.classList.add("doclib-sc-header");
    header.style.background = cfg.color;

    const body = document.createElement("div");
    body.classList.add("doclib-sc-body");

    const avatarRow = document.createElement("div");
    avatarRow.classList.add("doclib-sc-avatar-row");

    const avatar = document.createElement("div");
    avatar.classList.add("doclib-sc-avatar");
    if (this.data.avatar) {
      const img = document.createElement("img");
      img.src = this.data.avatar;
      img.alt = this.data.displayName;
      avatar.appendChild(img);
    } else {
      avatar.innerText = (this.data.displayName[0] || "U").toUpperCase();
    }

    const badge = document.createElement("div");
    badge.classList.add("doclib-sc-platform-badge");
    badge.style.background = cfg.color;
    badge.innerHTML = `${cfg.icon}<span>${cfg.label}</span>`;

    avatarRow.appendChild(avatar);
    avatarRow.appendChild(badge);

    const displayName = document.createElement("div");
    displayName.classList.add("doclib-sc-display-name");
    displayName.innerText = this.data.displayName;

    const username = document.createElement("div");
    username.classList.add("doclib-sc-username");
    username.innerText = `@${this.data.username}`;

    const bio = document.createElement("div");
    bio.classList.add("doclib-sc-bio");
    bio.innerText = this.data.bio;

    const stats = document.createElement("div");
    stats.classList.add("doclib-sc-stats");

    const followerStat = document.createElement("div");
    followerStat.classList.add("doclib-sc-stat");
    const followerNum = document.createElement("div");
    followerNum.classList.add("doclib-sc-stat-num");
    followerNum.innerText = this.data.followers;
    const followerLabel = document.createElement("div");
    followerLabel.classList.add("doclib-sc-stat-label");
    followerLabel.innerText = "Followers";
    followerStat.appendChild(followerNum);
    followerStat.appendChild(followerLabel);
    stats.appendChild(followerStat);

    body.appendChild(avatarRow);
    body.appendChild(displayName);
    body.appendChild(username);
    body.appendChild(bio);
    body.appendChild(stats);

    if (this.data.url) {
      body.style.cursor = "pointer";
      body.addEventListener("click", () => window.open(this.data.url, "_blank"));
    }

    this.wrapper.appendChild(header);
    this.wrapper.appendChild(body);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-sc-edit");

      const platRow = document.createElement("div");
      platRow.classList.add("doclib-sc-platform-row");
      const platforms: SocialPlatform[] = ["github", "twitter", "linkedin"];
      platforms.forEach((p) => {
        const btn = document.createElement("button");
        btn.classList.add("doclib-sc-platform-btn");
        if (this.data.platform === p) {
          btn.classList.add("active");
          btn.style.background = this.getPlatformConfig(p).color;
        }
        btn.innerText = this.getPlatformConfig(p).label;
        btn.addEventListener("click", () => {
          this.data.platform = p;
          this.buildUI();
        });
        platRow.appendChild(btn);
      });
      edit.appendChild(platRow);

      const fields: { key: keyof typeof this.data; label: string }[] = [
        { key: "displayName", label: "Display name" },
        { key: "username", label: "Username" },
        { key: "followers", label: "Followers" },
        { key: "avatar", label: "Avatar URL" },
        { key: "url", label: "Profile URL" },
        { key: "bio", label: "Bio" },
      ];

      fields.forEach(({ key, label }) => {
        const field = document.createElement("div");
        field.classList.add("doclib-sc-edit-field");
        if (key === "bio" || key === "url" || key === "avatar") field.style.gridColumn = "1 / -1";

        const lbl = document.createElement("label");
        lbl.innerText = label;

        const input = document.createElement("input");
        input.value = this.data[key] as string;
        input.addEventListener("input", () => {
          (this.data as any)[key] = input.value;
          this.buildUI();
        });

        field.appendChild(lbl);
        field.appendChild(input);
        edit.appendChild(field);
      });

      this.wrapper.appendChild(edit);
    }
  }

  save() {
    return this.data;
  }
}
