import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibPictureCorrections implements BlockTool {
  static readonly feature = {
    id: "DocLibPictureCorrections",
    title: "Picture Corrections",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="efd187594fc807ea"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="5,9 20,8 15,17 11,17 12,11 4,20"/></svg>',
    product: "doclib",
  } as const;

  static get toolbox() {
    return {
      title: "Picture Corrections",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="efd187594fc807ea"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="5,9 20,8 15,17 11,17 12,11 4,20"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibPictureCorrections";
  readonly title = "Picture Corrections";
  readonly category = "media" as const;
  readonly mode = "PictureCorrections";
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
    editor.blocks.insert("image", { title: this.title, effect: this.mode, url: "" });
  }
}
