import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibRemovePageNumbers implements BlockTool {
  static readonly feature = {
    id: "DocLibRemovePageNumbers",
    title: "DocLib RemovePageNumbers",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f3d2a9679427bf4b"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="9,10 20,5 16,9 8,11 4,9 9,18"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib Remove Page Numbers",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f3d2a9679427bf4b"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="9,10 20,5 16,9 8,11 4,9 9,18"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibRemovePageNumbers";
  readonly title = "DocLib Remove Page Numbers";
  readonly category = "layout" as const;
  readonly mode = "RemovePageNumbers";
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
    root.dataset.wordLayout = this.mode;
    window.dispatchEvent(
      new CustomEvent("doclib-layout-command", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
