export default class DocLibDragDrop {
  static readonly feature = {
    id: "DocLibDragDrop",
    title: "DocLib DragDrop",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="82ea11096c0f1850"><rect x="2" y="2" width="20" height="20" rx="3"/><polyline points="15,17 4,13 10,19 11,16 5,6 14,4"/></svg>',
    product: "doclib",
  } as const;

  private editor: any;
  private holder: HTMLElement | null = null;
  private dragPlaceholder: HTMLElement;
  private draggedBlock: HTMLElement | null = null;
  private initTimer: ReturnType<typeof setTimeout>;

  constructor(editor: any) {
    this.editor = editor;
    this.dragPlaceholder = document.createElement("div");
    this.dragPlaceholder.className = "doclib-drag-placeholder";

    if (!document.getElementById("doclib-dragdrop-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-dragdrop-styles";
      style.innerHTML = `
            .ce-block { position: relative; }
            .ce-toolbar__settings-btn--drag { cursor: grab !important; }
            .ce-toolbar__settings-btn--drag:active { cursor: grabbing !important; }
            .ce-block--dragging { opacity: 0.4; }
            .doclib-drag-placeholder { height: 4px; background: #3b82f6; border-radius: 2px; margin: 4px 0; transition: all 0.2s; }
        `;
      document.head.appendChild(style);
    }

    this.initTimer = setTimeout(() => this.init(), 500);
  }

  private init() {
    this.holder = document.querySelector(".codex-editor__redactor");
    if (!this.holder) return;

    const toolbar = document.querySelector(".ce-toolbar");
    if (!toolbar) return;

    document.addEventListener("mousedown", this.handleMouseDown);
    this.holder.addEventListener("dragstart", this.handleDragStart);
    this.holder.addEventListener("dragover", this.handleDragOver);
    this.holder.addEventListener("drop", this.handleDrop);
    this.holder.addEventListener("dragend", this.cleanup);
    document.addEventListener("mouseup", this.cleanup);
  }

  private handleMouseDown = (e: MouseEvent) => {
    const target = e.target as HTMLElement;
    const dragHandle = target.closest(".ce-toolbar__settings-btn");
    if (!dragHandle || !this.holder) return;
    const currentBlockIndex = this.editor.blocks.getCurrentBlockIndex();
    if (currentBlockIndex < 0) return;
    this.draggedBlock = this.holder.children[currentBlockIndex] as HTMLElement;
    if (this.draggedBlock) {
      this.draggedBlock.draggable = true;
      this.draggedBlock.classList.add("ce-block--dragging");
    }
  };

  private handleDragStart = (e: DragEvent) => {
    if (!this.draggedBlock) {
      e.preventDefault();
      return;
    }
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", "doclib-block");
    }
  };

  private handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    if (!this.draggedBlock) return;
    if (e.dataTransfer) e.dataTransfer.dropEffect = "move";
    const targetBlock = (e.target as HTMLElement).closest(".ce-block");
    if (!targetBlock || targetBlock === this.draggedBlock) return;
    const rect = targetBlock.getBoundingClientRect();
    const next = (e.clientY - rect.top) / (rect.bottom - rect.top) > 0.5;
    targetBlock.parentNode?.insertBefore(
      this.dragPlaceholder,
      next ? targetBlock.nextSibling : targetBlock,
    );
  };

  private handleDrop = async (e: DragEvent) => {
    e.preventDefault();
    if (!this.holder || !this.draggedBlock || !this.dragPlaceholder.parentNode) {
      this.cleanup();
      return;
    }
    const blocks = Array.from(this.holder.children).filter((element) =>
      element.classList.contains("ce-block"),
    );
    const fromIndex = blocks.indexOf(this.draggedBlock);
    this.dragPlaceholder.parentNode.insertBefore(
      this.draggedBlock,
      this.dragPlaceholder,
    );
    const movedBlocks = Array.from(this.holder.children).filter((element) =>
      element.classList.contains("ce-block"),
    );
    const toIndex = movedBlocks.indexOf(this.draggedBlock);
    if (fromIndex !== -1 && toIndex !== -1 && fromIndex !== toIndex) {
      await this.editor.blocks.move(toIndex, fromIndex);
    }
    this.cleanup();
  };

  private cleanup = () => {
    if (this.draggedBlock) {
      this.draggedBlock.draggable = false;
      this.draggedBlock.classList.remove("ce-block--dragging");
      this.draggedBlock = null;
    }
    if (this.dragPlaceholder.parentNode) {
      this.dragPlaceholder.parentNode.removeChild(this.dragPlaceholder);
    }
  };

  public destroy() {
    clearTimeout(this.initTimer);
    document.removeEventListener("mousedown", this.handleMouseDown);
    document.removeEventListener("mouseup", this.cleanup);
    this.holder?.removeEventListener("dragstart", this.handleDragStart);
    this.holder?.removeEventListener("dragover", this.handleDragOver);
    this.holder?.removeEventListener("drop", this.handleDrop);
    this.holder?.removeEventListener("dragend", this.cleanup);
    this.cleanup();
    this.holder = null;
  }
}
