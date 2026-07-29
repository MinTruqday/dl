import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibAlert implements BlockTool {
  static readonly feature = {
    id: "DocLibAlert",
    title: "DocLib Alert",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f11c9371f4fa509e"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="7,15 15,15 10,16 16,9 12,13 11,9"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private data: { type: string; message: string };
  private wrapper: HTMLElement | null = null;
  private messageEl: HTMLElement | null = null;

  static get toolbox() {
    return {
      title: "DocLib Alert",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f11c9371f4fa509e"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="7,15 15,15 10,16 16,9 12,13 11,9"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      type: data.type || "",
      message: data.message || "",
    };
  }

  private getStyles(type: string) {
    const styles: Record<string, string> = {
      primary:
        "background-color: #cce5ff; color: #004085; border: 1px solid #b8daff;",
      secondary:
        "background-color: #e2e3e5; color: #383d41; border: 1px solid #d6d8db;",
      info: "background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb;",
      success:
        "background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;",
      warning:
        "background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba;",
      danger:
        "background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;",
      light:
        "background-color: #fefefe; color: #818182; border: 1px solid #fdfdfe;",
      dark: "background-color: #d6d8d9; color: #1b1e21; border: 1px solid #c6c8ca;",
    };
    return styles[type] || styles.info;
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    const alertDiv = document.createElement("div");
    alertDiv.style.padding = "15px";
    alertDiv.style.borderRadius = "5px";
    alertDiv.style.margin = "10px 0";
    alertDiv.style.cssText += this.getStyles(this.data.type);

    this.messageEl = document.createElement("div");
    this.messageEl.contentEditable = "true";
    this.messageEl.innerHTML = this.data.message;
    this.messageEl.dataset.placeholder = "DocLib Text";
    this.messageEl.style.outline = "none";

    alertDiv.appendChild(this.messageEl);
    this.wrapper.appendChild(alertDiv);

    return this.wrapper;
  }

  renderSettings() {
    const settings = [
      { name: "primary", color: "#cce5ff" },
      { name: "secondary", color: "#e2e3e5" },
      { name: "info", color: "#d1ecf1" },
      { name: "success", color: "#d4edda" },
      { name: "warning", color: "#fff3cd" },
      { name: "danger", color: "#f8d7da" },
      { name: "light", color: "#fefefe" },
      { name: "dark", color: "#d6d8d9" },
    ];

    const wrapper = document.createElement("div");
    wrapper.style.display = "grid";
    wrapper.style.gridTemplateColumns = "repeat(4, 1fr)";
    wrapper.style.gap = "5px";
    wrapper.style.padding = "5px";

    settings.forEach((tune) => {
      const button = document.createElement("div");
      button.style.width = "24px";
      button.style.height = "24px";
      button.style.borderRadius = "50%";
      button.style.backgroundColor = tune.color;
      button.style.cursor = "pointer";
      button.style.border = "1px solid rgba(0,0,0,0.1)";
      button.title = tune.name;

      if (this.data.type === tune.name) {
        button.style.boxShadow = "0 0 0 2px #388ae5";
      }

      button.addEventListener("click", () => {
        this.data.type = tune.name;

        const alertDiv = this.wrapper?.firstChild as HTMLElement;
        if (alertDiv) {
          alertDiv.style.cssText = `padding: 15px; border-radius: 5px; margin: 10px 0; ${this.getStyles(tune.name)}`;
        }

        Array.from(wrapper.children).forEach(
          (btn: any) => (btn.style.boxShadow = "none"),
        );
        button.style.boxShadow = "0 0 0 2px #388ae5";
      });

      wrapper.appendChild(button);
    });

    return wrapper;
  }

  save(blockContent: HTMLElement) {
    return {
      type: this.data.type,
      message: this.messageEl ? this.messageEl.innerHTML : "",
    };
  }

  static get sanitize() {
    return {
      type: false,
      message: { br: true, b: true, i: true, a: true },
    };
  }
}
