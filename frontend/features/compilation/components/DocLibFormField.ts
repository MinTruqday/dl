import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibFormField implements BlockTool {
  static readonly feature = {
    id: "DocLibFormField",
    title: "Form Field",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="73044be28d02fb19"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="17,8 11,9 9,6 17,12 4,13 4,8"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Form Field",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="73044be28d02fb19"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="17,8 11,9 9,6 17,12 4,13 4,8"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibFormField";
  readonly title = "Form Field";
  readonly category = "format" as const;
  readonly mode = "FormField";
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
    const event = new CustomEvent("doclib-command", {
      cancelable: true,
      detail: {
        command: this.id,
        mode: this.mode,
        editor,
      },
    });
    window.dispatchEvent(event);
    if (!event.defaultPrevented) {
      throw new Error(`No handler registered for ${this.mode}`);
    }
  }
}
