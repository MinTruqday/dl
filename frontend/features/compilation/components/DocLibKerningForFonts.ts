import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibKerningForFonts implements BlockTool {
  static readonly feature = {
    id: "DocLibKerningForFonts",
    title: "Kerning For Fonts",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b02fe67c7bf4c2ca"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="10,17 13,9 8,10 11,19 12,12 11,12"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Kerning For Fonts",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b02fe67c7bf4c2ca"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="10,17 13,9 8,10 11,19 12,12 11,12"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibKerningForFonts";
  readonly title = "Kerning For Fonts";
  readonly category = "format" as const;
  readonly mode = "KerningForFonts";
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
    const selection = window.getSelection();
    const anchor = selection?.anchorNode;
    const element =
      anchor instanceof HTMLElement ? anchor : anchor?.parentElement || null;
    const block = element?.closest<HTMLElement>(".ce-block") || document.querySelector<HTMLElement>(".ce-block--focused");
    if (block) block.dataset.wordFormat = this.mode;
    window.dispatchEvent(
      new CustomEvent("doclib-format-command", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
