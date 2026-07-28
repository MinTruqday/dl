import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSensitivityLabel implements BlockTool {
  static readonly feature = {
    id: "DocLibSensitivityLabel",
    title: "DocLib SensitivityLabel",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="157ae05d04f0a66f"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="8,7 7,12 8,6 17,13 6,17 20,19"/></svg>',
    origin: "word-compatible",
  } as const;

  static get toolbox() {
    return {
      title: "DocLib Sensitivity Label",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="157ae05d04f0a66f"><rect x="6" y="6" width="12" height="12" rx="3"/><polyline points="8,7 7,12 8,6 17,13 6,17 20,19"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  readonly id = "DocLibSensitivityLabel";
  readonly title = "DocLib Sensitivity Label";
  readonly category = "security" as const;
  readonly mode = "SensitivityLabel";
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
    const root = document.querySelector<HTMLElement>(".codex-editor");
    if (root) root.dataset.wordSecurity = this.mode;
    window.dispatchEvent(
      new CustomEvent("doclib-security-command", {
        detail: { command: this.id, mode: this.mode },
      }),
    );
  }
}
