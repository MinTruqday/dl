export default class DocLibMultiBlockSelection {
  static readonly feature = {
    id: "DocLibMultiBlockSelection",
    title: "DocLib MultiBlockSelection",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="589bf88312af7e12"><rect x="5" y="5" width="14" height="14" rx="3"/><polyline points="7,6 14,16 5,9 11,5 9,15 12,7"/></svg>',
    product: "doclib",
  } as const;

  private editor: any;
  private holder: HTMLElement | null = null;
  private isSelecting: boolean = false;
  private startBlockIndex: number = -1;
  private currentSelection: Set<number> = new Set();
  private initTimer: ReturnType<typeof setTimeout>;

  constructor(editor: any) {
    this.editor = editor;

    if (!document.getElementById("doclib-multiselect-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-multiselect-styles";
      style.innerHTML = `
            .ce-block--selected .ce-block__content { background: rgba(59, 130, 246, 0.1); border-radius: 4px; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3); }
        `;
      document.head.appendChild(style);
    }

    this.initTimer = setTimeout(() => this.init(), 500);
  }

  private init() {
    this.holder = document.querySelector(".codex-editor__redactor");
    if (!this.holder) return;

    document.addEventListener("mousedown", this.handleMouseDown);
    document.addEventListener("mouseover", this.handleMouseOver);
    document.addEventListener("mouseup", this.handleMouseUp);
    document.addEventListener("keydown", this.handleKeyDown);
  }

  private handleMouseDown = (e: MouseEvent) => {
    if (!e.shiftKey) {
      this.clearSelection();
      return;
    }
    const block = (e.target as HTMLElement).closest(".ce-block");
    if (!block || !this.holder || !this.holder.contains(block)) return;
    e.preventDefault();
    this.isSelecting = true;
    const blocks = Array.from(this.holder.querySelectorAll(".ce-block"));
    this.startBlockIndex = blocks.indexOf(block);
    this.toggleSelection(this.startBlockIndex);
  };

  private handleMouseOver = (e: MouseEvent) => {
    if (!this.isSelecting || this.startBlockIndex === -1 || !this.holder)
      return;
    const block = (e.target as HTMLElement).closest(".ce-block");
    if (!block || !this.holder.contains(block)) return;
    const blocks = Array.from(this.holder.querySelectorAll(".ce-block"));
    this.selectRange(this.startBlockIndex, blocks.indexOf(block));
  };

  private handleMouseUp = () => {
    this.isSelecting = false;
  };

  private handleKeyDown = (e: KeyboardEvent) => {
    if (
      (e.key === "Backspace" || e.key === "Delete") &&
      this.currentSelection.size > 0
    ) {
      e.preventDefault();
      const indices = Array.from(this.currentSelection).sort((a, b) => b - a);
      indices.forEach((index) => {
        try {
          this.editor.blocks.delete(index);
        } catch (error) {
          console.warn("Could not delete block at index", index, error);
        }
      });
      this.clearSelection();
    }
    if (e.key === "Escape") this.clearSelection();
  };

  private toggleSelection(index: number) {
    if (this.currentSelection.has(index)) {
      this.currentSelection.delete(index);
    } else {
      this.currentSelection.add(index);
    }
    this.renderSelection();
  }

  private selectRange(start: number, end: number) {
    this.currentSelection.clear();
    const min = Math.min(start, end);
    const max = Math.max(start, end);
    for (let i = min; i <= max; i++) {
      this.currentSelection.add(i);
    }
    this.renderSelection();
  }

  private clearSelection() {
    this.currentSelection.clear();
    this.renderSelection();
    this.startBlockIndex = -1;
  }

  private renderSelection() {
    if (!this.holder) return;
    const blocks = Array.from(this.holder.querySelectorAll(".ce-block"));
    blocks.forEach((block, index) => {
      if (this.currentSelection.has(index)) {
        block.classList.add("ce-block--selected");
      } else {
        block.classList.remove("ce-block--selected");
      }
    });
  }

  public destroy() {
    clearTimeout(this.initTimer);
    document.removeEventListener("mousedown", this.handleMouseDown);
    document.removeEventListener("mouseover", this.handleMouseOver);
    document.removeEventListener("mouseup", this.handleMouseUp);
    document.removeEventListener("keydown", this.handleKeyDown);
    this.clearSelection();
    this.holder = null;
  }
}
