import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFocusLine implements BlockTool {
  static readonly feature = {
    id: "DocLibFocusLine",
    title: "Focus Line",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6f28f79d49bc68f4"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="13,10 13,8 9,5 6,10 14,15 16,15"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Focus Line",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="6f28f79d49bc68f4"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="13,10 13,8 9,5 6,10 14,15 16,15"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibFocusLine";
  readonly title = "Focus Line";
  readonly category = "view" as const;
  readonly mode = "FocusLine";
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
    root.dataset.wordView = this.mode;
    window.dispatchEvent(
      new CustomEvent("doclib-view-command", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
