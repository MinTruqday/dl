import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibActiveXComboBox implements BlockTool {
  static readonly feature = {
    id: "DocLibActiveXComboBox",
    title: "Active X Combo Box",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="af2b9d6b80d9126e"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="9,13 8,9 13,17 5,12 11,18 10,19"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Active X Combo Box",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="af2b9d6b80d9126e"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="9,13 8,9 13,17 5,12 11,18 10,19"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibActiveXComboBox";
  readonly title = "Active X Combo Box";
  readonly category = "automation" as const;
  readonly mode = "ActiveXComboBox";
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
    editor.blocks.insert("formDropdown", { label: this.title, options: [] });
  }
}
