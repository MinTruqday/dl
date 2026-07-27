import { API } from "@editorjs/editorjs";

export default class DocLibUndo {
  private editor: any;
  private history: any[] = [];
  private position: number = -1;
  private maxHistorySize: number = 50;
  private isUndoing: boolean = false;
  private observer: MutationObserver | null = null;
  private holder: HTMLElement | null = null;
  private undoBtn: HTMLButtonElement | null = null;
  private redoBtn: HTMLButtonElement | null = null;
  private wrapper: HTMLElement | null = null;
  private observerTimer: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;

  constructor({
    editor,
    maxHistorySize = 50,
  }: {
    editor: any;
    maxHistorySize?: number;
  }) {
    this.editor = editor;
    this.maxHistorySize = maxHistorySize;

    if (!document.getElementById("doclib-undo-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-undo-styles";
      style.innerHTML = `
            .doclib-undo-wrapper { position: fixed; bottom: 20px; right: 20px; display: flex; gap: 8px; z-index: 1000; background: #fff; padding: 6px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }
            .doclib-undo-btn { display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 6px; border: none; background: transparent; color: #475569; cursor: pointer; transition: all 0.2s; }
            .doclib-undo-btn:hover:not(:disabled) { background: #f1f5f9; color: #0f172a; }
            .doclib-undo-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        `;
      document.head.appendChild(style);
    }

    this.initialize();
  }

  private async initialize() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add("doclib-undo-wrapper");

    this.undoBtn = document.createElement("button");
    this.undoBtn.classList.add("doclib-undo-btn");
    this.undoBtn.innerHTML =
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6"></path><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"></path></svg>';
    this.undoBtn.title = "Undo (Cmd+Z)";
    this.undoBtn.disabled = true;

    this.redoBtn = document.createElement("button");
    this.redoBtn.classList.add("doclib-undo-btn");
    this.redoBtn.innerHTML =
      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 7v6h-6"></path><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3l3 2.7"></path></svg>';
    this.redoBtn.title = "Redo (Cmd+Shift+Z)";
    this.redoBtn.disabled = true;

    this.wrapper.appendChild(this.undoBtn);
    this.wrapper.appendChild(this.redoBtn);
    document.body.appendChild(this.wrapper);

    this.undoBtn.addEventListener("click", () => this.undo());
    this.redoBtn.addEventListener("click", () => this.redo());

    try {
      const initialData = await this.editor.save();
      if (this.destroyed) return;
      this.history.push(initialData);
      this.position = 0;
    } catch (error) {
      console.warn("Could not initialize undo history", error);
    }

    document.addEventListener("keydown", this.handleKeyDown);

    this.observerTimer = setTimeout(() => {
      if (this.destroyed) return;
      this.holder = document.querySelector(".codex-editor__redactor");
      if (this.holder) {
        this.observer = new MutationObserver(() => this.saveState());
        this.observer.observe(this.holder, {
          childList: true,
          subtree: true,
          characterData: true,
        });
      }
    }, 500);
  }

  private debounceTimer: any = null;
  private saveState() {
    if (this.isUndoing) return;

    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(async () => {
      try {
        const data = await this.editor.save();
        if (this.destroyed) return;

        const lastData = this.history[this.position];
        if (JSON.stringify(data.blocks) === JSON.stringify(lastData?.blocks))
          return;

        if (this.position < this.history.length - 1) {
          this.history = this.history.slice(0, this.position + 1);
        }

        this.history.push(data);
        if (this.history.length > this.maxHistorySize) {
          this.history.shift();
        } else {
          this.position++;
        }
        this.updateUI();
      } catch (error) {
        console.warn("Could not save undo state", error);
      }
    }, 400);
  }

  private handleKeyDown = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "z") {
      e.preventDefault();
      if (e.shiftKey) {
        this.redo();
      } else {
        this.undo();
      }
    }
    if ((e.metaKey || e.ctrlKey) && e.key === "y") {
      e.preventDefault();
      this.redo();
    }
  };

  public async undo() {
    if (this.position > 0) {
      this.isUndoing = true;
      this.position--;
      await this.editor.render(this.history[this.position]);
      this.updateUI();
      setTimeout(() => (this.isUndoing = false), 100);
    }
  }

  public async redo() {
    if (this.position < this.history.length - 1) {
      this.isUndoing = true;
      this.position++;
      await this.editor.render(this.history[this.position]);
      this.updateUI();
      setTimeout(() => (this.isUndoing = false), 100);
    }
  }

  private updateUI() {
    if (this.undoBtn) this.undoBtn.disabled = this.position <= 0;
    if (this.redoBtn)
      this.redoBtn.disabled = this.position >= this.history.length - 1;
  }

  public destroy() {
    this.destroyed = true;
    document.removeEventListener("keydown", this.handleKeyDown);
    if (this.observerTimer) clearTimeout(this.observerTimer);
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    this.observer?.disconnect();
    this.wrapper?.remove();
    this.observer = null;
    this.wrapper = null;
  }
}
