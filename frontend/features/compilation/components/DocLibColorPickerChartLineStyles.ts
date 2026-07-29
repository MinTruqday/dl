import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibColorPickerChartLineStyles implements BlockTool {
  static readonly feature = {
    id: "DocLibColorPickerChartLineStyles",
    title: "DocLib ColorPickerChartLineStyles",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ca20e4c33450190a"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="19,19 11,12 5,16 12,14 19,15 17,11"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib ColorPickerChartLineStyles",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ca20e4c33450190a"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="19,19 11,12 5,16 12,14 19,15 17,11"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibColorPickerChartLineStyles";
  readonly title = "DocLib ColorPickerChartLineStyles";
  readonly category = "media" as const;
  readonly mode = "ColorPickerChartLineStyles";
  readonly requiresSelection = false;
  readonly microsoftControlId = "ColorPickerChartLineStyles";
  readonly controlType = "gallery";
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
