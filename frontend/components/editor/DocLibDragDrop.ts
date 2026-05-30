export default class DocLibDragDrop {
  private editor: any;
  private holder: HTMLElement | null = null;
  private dragPlaceholder: HTMLElement;
  private draggedBlock: HTMLElement | null = null;

  constructor(editor: any) {
    this.editor = editor;
    this.dragPlaceholder = document.createElement('div');
    this.dragPlaceholder.className = 'doclib-drag-placeholder';
    
    if (!document.getElementById('doclib-dragdrop-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-dragdrop-styles';
        style.innerHTML = `
            .ce-block { position: relative; }
            .ce-toolbar__settings-btn--drag { cursor: grab !important; }
            .ce-toolbar__settings-btn--drag:active { cursor: grabbing !important; }
            .ce-block--dragging { opacity: 0.4; }
            .doclib-drag-placeholder { height: 4px; background: #3b82f6; border-radius: 2px; margin: 4px 0; transition: all 0.2s; }
        `;
        document.head.appendChild(style);
    }
    
    setTimeout(() => this.init(), 500);
  }
  
  private init() {
      this.holder = document.querySelector('.codex-editor__redactor');
      if (!this.holder) return;

      const toolbar = document.querySelector('.ce-toolbar');
      if (!toolbar) return;

      
      document.addEventListener('mousedown', (e: MouseEvent) => {
          const target = e.target as HTMLElement;
          const dragHandle = target.closest('.ce-toolbar__settings-btn');
          
          if (dragHandle) {
              const currentBlockIndex = this.editor.blocks.getCurrentBlockIndex();
              if (currentBlockIndex < 0) return;
              
              this.draggedBlock = this.holder!.children[currentBlockIndex] as HTMLElement;
              if (this.draggedBlock) {
                  this.draggedBlock.draggable = true;
                  this.draggedBlock.classList.add('ce-block--dragging');
              }
          }
      });

      this.holder.addEventListener('dragstart', (e: DragEvent) => {
          if (!this.draggedBlock) {
              e.preventDefault();
              return;
          }
          if (e.dataTransfer) {
              e.dataTransfer.effectAllowed = 'move';
              e.dataTransfer.setData('text/plain', 'doclib-block');
          }
      });

      this.holder.addEventListener('dragover', (e: DragEvent) => {
          e.preventDefault();
          if (!this.draggedBlock) return;
          
          if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
          
          const target = e.target as HTMLElement;
          const targetBlock = target.closest('.ce-block');
          
          if (targetBlock && targetBlock !== this.draggedBlock) {
              const rect = targetBlock.getBoundingClientRect();
              const next = (e.clientY - rect.top) / (rect.bottom - rect.top) > 0.5;
              
              if (next) {
                  targetBlock.parentNode?.insertBefore(this.dragPlaceholder, targetBlock.nextSibling);
              } else {
                  targetBlock.parentNode?.insertBefore(this.dragPlaceholder, targetBlock);
              }
          }
      });

      this.holder.addEventListener('drop', async (e: DragEvent) => {
          e.preventDefault();
          if (!this.draggedBlock || !this.dragPlaceholder.parentNode) {
              this.cleanup();
              return;
          }
          
          
          const blocks = Array.from(this.holder!.children).filter(c => c.classList.contains('ce-block'));
          const fromIndex = blocks.indexOf(this.draggedBlock);
          
          this.dragPlaceholder.parentNode.insertBefore(this.draggedBlock, this.dragPlaceholder);
          
          const newBlocks = Array.from(this.holder!.children).filter(c => c.classList.contains('ce-block'));
          const toIndex = newBlocks.indexOf(this.draggedBlock);
          
          if (fromIndex !== -1 && toIndex !== -1 && fromIndex !== toIndex) {
              await this.editor.blocks.move(toIndex, fromIndex);
          }
          
          this.cleanup();
      });

      this.holder.addEventListener('dragend', () => this.cleanup());
      document.addEventListener('mouseup', () => this.cleanup());
  }
  
  private cleanup() {
      if (this.draggedBlock) {
          this.draggedBlock.draggable = false;
          this.draggedBlock.classList.remove('ce-block--dragging');
          this.draggedBlock = null;
      }
      if (this.dragPlaceholder.parentNode) {
          this.dragPlaceholder.parentNode.removeChild(this.dragPlaceholder);
      }
  }
}
