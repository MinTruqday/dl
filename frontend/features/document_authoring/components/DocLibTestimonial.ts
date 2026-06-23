import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTestimonial implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    author: string;
    role: string;
    avatar: string;
    content: string;
    rating: number;
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Testimonial",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
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
      author: data.author || "",
      role: data.role || "",
      avatar: data.avatar || "",
      content: data.content || "",
      rating: data.rating || 5,
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-testimonial-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-testimonial-styles";
      style.innerHTML = `
            .doclib-tm-wrapper { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin: 24px 0; text-align: center; position: relative; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
            .doclib-tm-wrapper::before { content: '""'; position: absolute; top: 16px; left: 16px; font-size: 60px; color: #cbd5e1; font-family: serif; line-height: 1; opacity: 0.5; }
            .doclib-tm-stars { display: flex; justify-content: center; gap: 4px; color: #fbbf24; margin-bottom: 16px; }
            .doclib-tm-star { width: 20px; height: 20px; cursor: pointer; }
            .doclib-tm-content { font-size: 1.1em; font-style: italic; color: #334155; line-height: 1.6; margin-bottom: 24px; outline: none; position: relative; z-index: 1; }
            .doclib-tm-content:empty::before { content: 'Enter customer review content'; color: #94a3b8; }
            .doclib-tm-author-box { display: flex; align-items: center; justify-content: center; gap: 12px; }
            .doclib-tm-avatar { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; background: #e2e8f0; cursor: pointer; border: 2px solid #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .doclib-tm-info { text-align: left; }
            .doclib-tm-name { font-weight: 700; color: #0f172a; outline: none; font-size: 15px; }
            .doclib-tm-name:empty::before { content: 'Customer name'; color: #94a3b8; }
            .doclib-tm-role { font-size: 13px; color: #64748b; outline: none; }
            .doclib-tm-role:empty::before { content: 'Position/Company'; color: #94a3b8; }
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
    container.classList.add("doclib-tm-wrapper");

    const stars = document.createElement("div");
    stars.classList.add("doclib-tm-stars");
    for (let i = 1; i <= 5; i++) {
      const star = document.createElement("svg");
      star.classList.add("doclib-tm-star");
      star.setAttribute("viewBox", "0 0 24 24");
      star.setAttribute("stroke", "currentColor");
      star.setAttribute("stroke-width", "2");
      star.setAttribute(
        "fill",
        i <= this.data.rating ? "currentColor" : "none",
      );
      star.innerHTML =
        '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>';

      if (!this.readOnly) {
        star.addEventListener("click", () => {
          this.data.rating = i;
          this.buildUI();
        });
      }
      stars.appendChild(star);
    }
    container.appendChild(stars);

    const content = document.createElement("div");
    content.classList.add("doclib-tm-content");
    content.contentEditable = !this.readOnly ? "true" : "false";
    content.innerHTML = this.data.content;
    content.addEventListener(
      "input",
      () => (this.data.content = content.innerHTML),
    );
    container.appendChild(content);

    const authorBox = document.createElement("div");
    authorBox.classList.add("doclib-tm-author-box");

    const avatar = document.createElement("img");
    avatar.classList.add("doclib-tm-avatar");
    avatar.src =
      this.data.avatar ||
      "https://ui-avatars.com/api/?name=User&background=cbd5e1&color=fff";
    if (!this.readOnly) {
      avatar.addEventListener("click", () => {
        const url = prompt("Enter customer Avatar URL:", this.data.avatar);
        if (url !== null) {
          this.data.avatar = url;
          this.buildUI();
        }
      });
    }
    authorBox.appendChild(avatar);

    const info = document.createElement("div");
    info.classList.add("doclib-tm-info");

    const name = document.createElement("div");
    name.classList.add("doclib-tm-name");
    name.contentEditable = !this.readOnly ? "true" : "false";
    name.innerHTML = this.data.author;
    name.addEventListener("input", () => (this.data.author = name.innerHTML));
    info.appendChild(name);

    const role = document.createElement("div");
    role.classList.add("doclib-tm-role");
    role.contentEditable = !this.readOnly ? "true" : "false";
    role.innerHTML = this.data.role;
    role.addEventListener("input", () => (this.data.role = role.innerHTML));
    info.appendChild(role);

    authorBox.appendChild(info);
    container.appendChild(authorBox);

    this.wrapper.appendChild(container);
  }

  save() {
    return this.data;
  }
}
