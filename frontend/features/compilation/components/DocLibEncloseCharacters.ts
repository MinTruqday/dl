import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibEncloseCharacters implements BlockTool {
  static readonly feature = {
    id: "DocLibEncloseCharacters",
    title: "DocLib EncloseCharacters",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="dc0e681fe73c1ff1"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="20,18 6,18 14,13 18,7 11,19 9,16"/></svg>',
    origin: "word-compatible",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib Enclose Characters",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="dc0e681fe73c1ff1"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="20,18 6,18 14,13 18,7 11,19 9,16"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibEncloseCharacters";
  readonly title = "DocLib Enclose Characters";
  readonly category = "format" as const;
  readonly mode = "EncloseCharacters";
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
    const block = element?.closest<HTMLElement>(".ce-block") || document.querySelector<HTMLElement>(".ce-block--focused");
    if (block) block.dataset.wordFormat = this.mode;
    window.dispatchEvent(
      new CustomEvent("doclib-format-command", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
