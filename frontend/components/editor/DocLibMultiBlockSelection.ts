export default class DocLibMultiBlockSelection {
  private editor: any;
  private holder: HTMLElement | null = null;
  private isSelecting: boolean = false;
  private startBlockIndex: number = -1;
  private currentSelection: Set<number> = new Set();
  
  constructor(editor: any) {
    this.editor = editor;
    
    if (!document.getElementById('doclib-multiselect-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-multiselect-styles';
        style.innerHTML = `
            .ce-block--selected .ce-block__content { background: rgba(59, 130, 246, 0.1); border-radius: 4px; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3); }
        `;
        document.head.appendChild(style);
    }
    
    setTimeout(() => this.init(), 500);
  }
  
  private init() {
      this.holder = document.querySelector('.codex-editor__redactor');
      if (!this.holder) return;

      document.addEventListener('mousedown', (e: MouseEvent) => {
          // If shift key is held and we click a block
          if (e.shiftKey) {
              const target = e.target as HTMLElement;
              const blockEl = target.closest('.ce-block');
              if (blockEl) {
                  e.preventDefault();
                  this.isSelecting = true;
                  const blocks = Array.from(this.holder!.children);
                  this.startBlockIndex = blocks.indexOf(blockEl);
                  this.toggleSelection(this.startBlockIndex);
              }
          } else {
              this.clearSelection();
          }
      });
      
      document.addEventListener('mouseover', (e: MouseEvent) => {
          if (!this.isSelecting || this.startBlockIndex === -1) return;
          
          const target = e.target as HTMLElement;
          const blockEl = target.closest('.ce-block');
          if (blockEl) {
              const blocks = Array.from(this.holder!.children);
              const hoverIndex = blocks.indexOf(blockEl);
              this.selectRange(this.startBlockIndex, hoverIndex);
          }
      });
      
      document.addEventListener('mouseup', () => {
          this.isSelecting = false;
      });
      
      // Handle bulk delete
      document.addEventListener('keydown', (e: KeyboardEvent) => {
          if ((e.key === 'Backspace' || e.key === 'Delete') && this.currentSelection.size > 0) {
              e.preventDefault();
              const indices = Array.from(this.currentSelection).sort((a, b) => b - a);
              indices.forEach(index => {
                  this.editor.blocks.delete(index);
              });
              this.clearSelection();
          }
          if (e.key === 'Escape') {
              this.clearSelection();
          }
      });
  }
  
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
      const blocks = Array.from(this.holder.children);
      blocks.forEach((block, index) => {
          if (this.currentSelection.has(index)) {
              block.classList.add('ce-block--selected');
          } else {
              block.classList.remove('ce-block--selected');
          }
      });
  }
}
