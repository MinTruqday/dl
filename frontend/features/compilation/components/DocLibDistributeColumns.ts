import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibDistributeColumns implements BlockTool {
  static readonly feature = {
    id: "DocLibDistributeColumns",
    title: "DocLib DistributeColumns",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a24285adf7a27c64"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="13,19 18,7 13,13 9,19 19,6 20,10"/></svg>',
    origin: "word-compatible",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib Distribute Columns",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="a24285adf7a27c64"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="13,19 18,7 13,13 9,19 19,6 20,10"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibDistributeColumns";
  readonly title = "DocLib Distribute Columns";
  readonly category = "table" as const;
  readonly mode = "DistributeColumns";
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
    const table = element?.closest<HTMLTableElement>("table");
    if (!table) throw new Error("Select a table before running this command");
    Array.from(table.rows).forEach((row) => Array.from(row.cells).forEach((cell) => (cell.style.width = row.cells.length ? `${100 / row.cells.length}%` : "auto")));
  }
}
