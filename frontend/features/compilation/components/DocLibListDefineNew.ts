import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibListDefineNew implements BlockTool {
  static readonly feature = {
    id: "DocLibListDefineNew",
    title: "DocLib ListDefineNew",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e8285e7786962aa1"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="15,10 13,4 19,18 12,12 4,13 16,18"/></svg>',
    origin: "microsoft-word",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib ListDefineNew",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="e8285e7786962aa1"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="15,10 13,4 19,18 12,12 4,13 16,18"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibListDefineNew";
  readonly title = "DocLib ListDefineNew";
  readonly category = "format" as const;
  readonly mode = "ListDefineNew";
  readonly requiresSelection = false;
  readonly microsoftControlId = "ListDefineNew";
  readonly controlType = "button";
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
    const event = new CustomEvent("doclib-microsoft-word-control", {
      cancelable: true,
      detail: {
        command: this.id,
        controlId: this.microsoftControlId,
        controlType: this.controlType,
        editor,
      },
    });
    window.dispatchEvent(event);
    if (!event.defaultPrevented) {
      throw new Error(`No handler registered for ${this.microsoftControlId}`);
    }
  }
}
