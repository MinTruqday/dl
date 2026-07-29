import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibReadAloud implements BlockTool {
  static readonly feature = {
    id: "DocLibReadAloud",
    title: "Read Aloud",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="3d529287fa15a2f5"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="14,18 14,20 16,8 13,11 16,16 6,4"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Read Aloud",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="3d529287fa15a2f5"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="14,18 14,20 16,8 13,11 16,16 6,4"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibReadAloud";
  readonly title = "Read Aloud";
  readonly category = "view" as const;
  readonly mode = "ReadAloud";
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
    const text = window.getSelection()?.toString() || root.textContent?.trim() || "";
    window.speechSynthesis.cancel();
    if (text) window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
    window.dispatchEvent(
      new CustomEvent("doclib-view-command", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
