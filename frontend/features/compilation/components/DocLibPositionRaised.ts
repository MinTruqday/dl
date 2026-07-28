import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibPositionRaised implements BlockTool {
  static readonly feature = {
    id: "DocLibPositionRaised",
    title: "DocLib PositionRaised",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f92b74d2cb54e069"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="15,13 18,10 20,20 7,7 7,15 12,5"/></svg>',
    origin: "word-compatible",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib Position Raised",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="f92b74d2cb54e069"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="15,13 18,10 20,20 7,7 7,15 12,5"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibPositionRaised";
  readonly title = "DocLib Position Raised";
  readonly category = "format" as const;
  readonly mode = "PositionRaised";
  readonly requiresSelection = true;
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
    if (block) block.style.transform = "translateY(-0.2em)";
  }
}
