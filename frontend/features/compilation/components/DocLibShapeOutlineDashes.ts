import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibShapeOutlineDashes implements BlockTool {
  static readonly feature = {
    id: "DocLibShapeOutlineDashes",
    title: "DocLib ShapeOutlineDashes",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="834c47f8294adf54"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="16,12 7,14 11,10 6,20 17,19 8,17"/></svg>',
    origin: "word-compatible",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib Shape Outline Dashes",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="834c47f8294adf54"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="16,12 7,14 11,10 6,20 17,19 8,17"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibShapeOutlineDashes";
  readonly title = "DocLib Shape Outline Dashes";
  readonly category = "media" as const;
  readonly mode = "ShapeOutlineDashes";
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
    const block = element?.closest<HTMLElement>(".ce-block");
    const image = element?.closest<HTMLImageElement>("img") || block?.querySelector<HTMLImageElement>("img");
    if (image) {
      image.dataset.wordEffect = this.mode;
      image.style.setProperty("--doclib-media-effect", this.mode);
      image.dispatchEvent(new InputEvent("input", { bubbles: true }));
      return;
    }
    editor.blocks.insert("shape", { title: this.title, effect: this.mode, url: "" });
  }
}
