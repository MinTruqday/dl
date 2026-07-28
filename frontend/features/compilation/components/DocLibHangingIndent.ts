import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibHangingIndent implements BlockTool {
  static readonly feature = {
    id: "DocLibHangingIndent",
    title: "DocLib HangingIndent",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="76be1b8b3bae1815"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="20,7 14,7 12,8 11,8 12,16 15,7"/></svg>',
    origin: "microsoft-word",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib Hanging Indent",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="76be1b8b3bae1815"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="20,7 14,7 12,8 11,8 12,16 15,7"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibHangingIndent";
  readonly title = "DocLib Hanging Indent";
  readonly category = "layout" as const;
  readonly mode = "HangingIndent";
  readonly requiresSelection = false;
  private api?: API;
  private data: BlockToolData;
  private wrapper: HTMLElement | null = null;

  constructor(
    { api, data }: { api?: API; data?: BlockToolData } = {},
  ) {
    this.api = api;
    this.data = data || {};
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add("cdx-block", "doclib-word-command");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = this.title;
    button.classList.add("doclib-word-command__button");
    button.dataset.applied = this.data.applied === true ? "true" : "false";
    button.addEventListener("click", () => {
      if (!this.api || !this.wrapper) return;
      void this.execute(this.api)
        .then(() => {
          if (!this.wrapper) return;
          this.wrapper.dataset.applied = "true";
          button.dataset.applied = "true";
          this.data = {
            feature: this.id,
            mode: this.mode,
            applied: true,
          };
        })
        .catch((error) => {
          if (this.wrapper) {
            this.wrapper.dataset.error =
              error instanceof Error ? error.message : "Command failed";
          }
        });
    });
    this.wrapper.appendChild(button);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return {
      feature: this.id,
      mode: this.mode,
      applied: blockContent.dataset.applied === "true",
    };
  }

  validate(savedData: BlockToolData) {
    return savedData.feature === this.id && savedData.mode === this.mode;
  }

  async execute(editor: any) {
    const root = document.querySelector<HTMLElement>(".codex-editor");
    if (!root) throw new Error("Editor is not ready");
    root.style.textIndent = "-2em";
    window.dispatchEvent(
      new CustomEvent("doclib-layout-command", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
