import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibBioLink implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    name: string;
    bio: string;
    avatar: string;
    links: { label: string; url: string; icon: string; color: string }[];
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Bio Link",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      name: data?.name || "",
      bio: data?.bio || "",
      avatar: data?.avatar || "",
      links: data?.links || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-biolink-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-biolink-styles";
      style.innerHTML = `
        .doclib-bl-wrapper { border: 1px solid #e2e8f0; border-radius: 12px; padding: 28px 20px; background: #fafafa; margin: 12px 0; max-width: 420px; margin-left: auto; margin-right: auto; }
        .doclib-bl-profile { text-align: center; margin-bottom: 20px; }
        .doclib-bl-avatar { width: 72px; height: 72px; border-radius: 50%; background: #e2e8f0; margin: 0 auto 10px; overflow: hidden; display: flex; align-items: center; justify-content: center; font-size: 28px; border: 3px solid #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .doclib-bl-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .doclib-bl-name { font-size: 18px; font-weight: 700; color: #0f172a; }
        .doclib-bl-bio { font-size: 13px; color: #64748b; margin-top: 4px; }
        .doclib-bl-links { display: flex; flex-direction: column; gap: 10px; }
        .doclib-bl-link { display: flex; align-items: center; gap: 10px; padding: 12px 18px; border-radius: 10px; color: #fff; font-size: 14px; font-weight: 600; text-decoration: none; transition: opacity 0.15s; cursor: pointer; }
        .doclib-bl-link:hover { opacity: 0.88; }
        .doclib-bl-link-icon { font-size: 18px; }
        .doclib-bl-edit { border-top: 1px solid #e2e8f0; margin-top: 20px; padding-top: 16px; }
        .doclib-bl-field { display: flex; flex-direction: column; gap: 3px; margin-bottom: 8px; }
        .doclib-bl-field label { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; }
        .doclib-bl-field input { padding: 7px 9px; border: 1px solid #e2e8f0; border-radius: 5px; font-size: 12px; outline: none; }
        .doclib-bl-link-row { display: grid; grid-template-columns: 28px 1fr 1fr 28px; gap: 6px; align-items: center; margin-bottom: 5px; }
        .doclib-bl-link-input { padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 12px; outline: none; width: 100%; box-sizing: border-box; }
        .doclib-bl-del { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; }
        .doclib-bl-add-btn { padding: 6px 12px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 5px; font-size: 11px; cursor: pointer; margin-top: 4px; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-bl-wrapper");

    const profile = document.createElement("div");
    profile.classList.add("doclib-bl-profile");

    const avatar = document.createElement("div");
    avatar.classList.add("doclib-bl-avatar");
    if (this.data.avatar) {
      const img = document.createElement("img");
      img.src = this.data.avatar;
      img.alt = this.data.name;
      avatar.appendChild(img);
    } else {
      avatar.innerText = (this.data.name[0] || "?").toUpperCase();
    }

    const name = document.createElement("div");
    name.classList.add("doclib-bl-name");
    name.innerText = this.data.name;

    const bio = document.createElement("div");
    bio.classList.add("doclib-bl-bio");
    bio.innerText = this.data.bio;

    profile.appendChild(avatar);
    profile.appendChild(name);
    profile.appendChild(bio);

    const links = document.createElement("div");
    links.classList.add("doclib-bl-links");

    this.data.links.forEach((link) => {
      const el = document.createElement("a");
      el.classList.add("doclib-bl-link");
      el.style.background = link.color;
      el.href = link.url;
      el.target = "_blank";
      el.innerHTML = `<span class="doclib-bl-link-icon">${link.icon}</span><span>${link.label}</span>`;
      links.appendChild(el);
    });

    this.wrapper.appendChild(profile);
    this.wrapper.appendChild(links);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-bl-edit");

      const profileFields: { key: "name" | "bio" | "avatar"; label: string }[] = [
        { key: "name", label: "Name" },
        { key: "bio", label: "Description" },
        { key: "avatar", label: "Avatar URL" },
      ];

      profileFields.forEach(({ key, label }) => {
        const field = document.createElement("div");
        field.classList.add("doclib-bl-field");
        const lbl = document.createElement("label");
        lbl.innerText = label;
        const input = document.createElement("input");
        input.value = this.data[key];
        let t: ReturnType<typeof setTimeout>;
        input.addEventListener("input", () => {
          this.data[key] = input.value;
          clearTimeout(t);
          t = setTimeout(() => this.buildUI(), 300);
        });
        field.appendChild(lbl);
        field.appendChild(input);
        edit.appendChild(field);
      });

      const linkHeader = document.createElement("div");
      linkHeader.style.cssText = "font-size:10px;font-weight:600;color:#94a3b8;text-transform:uppercase;margin-bottom:4px;";
      linkHeader.innerText = "Links";
      edit.appendChild(linkHeader);

      const linkRows = document.createElement("div");

      const renderLinkRows = () => {
        linkRows.innerHTML = "";
        this.data.links.forEach((link, i) => {
          const row = document.createElement("div");
          row.classList.add("doclib-bl-link-row");

          const iconInput = document.createElement("input");
          iconInput.classList.add("doclib-bl-link-input");
          iconInput.value = link.icon;
          iconInput.style.textAlign = "center";
          iconInput.addEventListener("input", () => { link.icon = iconInput.value; this.buildUI(); });

          const labelInput = document.createElement("input");
          labelInput.classList.add("doclib-bl-link-input");
          labelInput.value = link.label;
          labelInput.placeholder = "DocLib URL";
          labelInput.addEventListener("input", () => { link.label = labelInput.value; this.buildUI(); });

          const urlInput = document.createElement("input");
          urlInput.classList.add("doclib-bl-link-input");
          urlInput.value = link.url;
          urlInput.placeholder = "DocLib URL";
          urlInput.addEventListener("input", () => { link.url = urlInput.value; });

          const del = document.createElement("button");
          del.classList.add("doclib-bl-del");
          del.innerText = "x";
          del.addEventListener("click", () => { this.data.links.splice(i, 1); renderLinkRows(); this.buildUI(); });

          row.appendChild(iconInput);
          row.appendChild(labelInput);
          row.appendChild(urlInput);
          row.appendChild(del);
          linkRows.appendChild(row);
        });

        const addBtn = document.createElement("button");
        addBtn.classList.add("doclib-bl-add-btn");
        addBtn.innerText = "Add link";
        addBtn.addEventListener("click", () => {
          this.data.links.push({ label: "New link", url: "https://", icon: "", color: "#475569" });
          renderLinkRows();
          this.buildUI();
        });
        linkRows.appendChild(addBtn);
      };

      renderLinkRows();
      edit.appendChild(linkRows);
      this.wrapper.appendChild(edit);
    }
  }

  save() {
    return this.data;
  }
}
