import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibDrawing implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { image: string };
  private canvas: HTMLCanvasElement | null = null;
  private ctx: CanvasRenderingContext2D | null = null;
  private isDrawing: boolean = false;

  static get toolbox() {
    return {
      title: 'DocLib Drawing',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19l7-7 3 3-7 7-3-3z"></path><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"></path><path d="M2 2l7.586 7.586"></path><circle cx="11" cy="11" r="2"></circle></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = { image: data.image || '' };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-drawing-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-drawing-styles';
        style.innerHTML = `
            .doclib-drawing-wrapper { margin: 16px 0; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; background: #fff; }
            .doclib-drawing-canvas { width: 100%; height: 300px; display: block; cursor: crosshair; touch-action: none; background: #f8fafc; }
            .doclib-drawing-controls { padding: 8px 16px; background: #f1f5f9; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; }
            .doclib-drawing-btn { font-size: 13px; padding: 4px 12px; border: 1px solid #cbd5e1; background: #fff; border-radius: 4px; cursor: pointer; transition: background 0.2s; }
            .doclib-drawing-btn:hover { background: #e2e8f0; }
            .doclib-drawing-colors { display: flex; gap: 8px; }
            .doclib-drawing-color { width: 24px; height: 24px; border-radius: 50%; cursor: pointer; border: 2px solid transparent; }
            .doclib-drawing-color.active { border-color: #3b82f6; transform: scale(1.1); }
            .doclib-drawing-readonly-img { width: 100%; height: auto; display: block; }
        `;
        document.head.appendChild(style);
    }
    
    this.buildUI();
    return this.wrapper;
  }
  
  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      const container = document.createElement('div');
      container.classList.add('doclib-drawing-wrapper');
      
      if (this.api.readOnly.toggle && this.data.image) {
          const img = document.createElement('img');
          img.classList.add('doclib-drawing-readonly-img');
          img.src = this.data.image;
          container.appendChild(img);
          this.wrapper.appendChild(container);
          return;
      }
      
      const controls = document.createElement('div');
      controls.classList.add('doclib-drawing-controls');
      
      const colorsDiv = document.createElement('div');
      colorsDiv.classList.add('doclib-drawing-colors');
      const colors = ['#0f172a', '#ef4444', '#3b82f6', '#22c55e', '#eab308'];
      let currentColor = '#0f172a';
      
      colors.forEach((c) => {
          const cBtn = document.createElement('div');
          cBtn.classList.add('doclib-drawing-color');
          cBtn.style.backgroundColor = c;
          if (c === currentColor) cBtn.classList.add('active');
          cBtn.addEventListener('click', () => {
              currentColor = c;
              if (this.ctx) this.ctx.strokeStyle = c;
              Array.from(colorsDiv.children).forEach(child => child.classList.remove('active'));
              cBtn.classList.add('active');
          });
          colorsDiv.appendChild(cBtn);
      });
      
      const clearBtn = document.createElement('button');
      clearBtn.classList.add('doclib-drawing-btn');
      clearBtn.innerText = 'Delete draft';
      clearBtn.addEventListener('click', () => {
          if (this.ctx && this.canvas) {
              this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
              this.data.image = '';
          }
      });
      
      controls.appendChild(colorsDiv);
      controls.appendChild(clearBtn);
      container.appendChild(controls);
      
      this.canvas = document.createElement('canvas');
      this.canvas.classList.add('doclib-drawing-canvas');
      container.appendChild(this.canvas);
      
      this.wrapper.appendChild(container);
      
      
      setTimeout(() => {
          if (!this.canvas) return;
          this.canvas.width = this.canvas.offsetWidth;
          this.canvas.height = this.canvas.offsetHeight;
          this.ctx = this.canvas.getContext('2d');
          if (!this.ctx) return;
          
          this.ctx.lineCap = 'round';
          this.ctx.lineJoin = 'round';
          this.ctx.lineWidth = 3;
          this.ctx.strokeStyle = currentColor;
          
          if (this.data.image) {
              const img = new Image();
              img.onload = () => this.ctx?.drawImage(img, 0, 0);
              img.src = this.data.image;
          }
          
          const startDrawing = (e: MouseEvent | TouchEvent) => {
              this.isDrawing = true;
              draw(e);
          };
          
          const stopDrawing = () => {
              this.isDrawing = false;
              if (this.ctx) this.ctx.beginPath();
              if (this.canvas) this.data.image = this.canvas.toDataURL('image/png');
          };
          
          const draw = (e: MouseEvent | TouchEvent) => {
              if (!this.isDrawing || !this.ctx || !this.canvas) return;
              e.preventDefault();
              
              const rect = this.canvas.getBoundingClientRect();
              let x = 0, y = 0;
              
              if (e instanceof MouseEvent) {
                  x = e.clientX - rect.left;
                  y = e.clientY - rect.top;
              } else if (e instanceof TouchEvent) {
                  x = e.touches[0].clientX - rect.left;
                  y = e.touches[0].clientY - rect.top;
              }
              
              this.ctx.lineTo(x, y);
              this.ctx.stroke();
              this.ctx.beginPath();
              this.ctx.moveTo(x, y);
          };
          
          this.canvas.addEventListener('mousedown', startDrawing);
          this.canvas.addEventListener('mousemove', draw);
          this.canvas.addEventListener('mouseup', stopDrawing);
          this.canvas.addEventListener('mouseout', stopDrawing);
          
          this.canvas.addEventListener('touchstart', startDrawing);
          this.canvas.addEventListener('touchmove', draw);
          this.canvas.addEventListener('touchend', stopDrawing);
      }, 0);
  }

  save() { return this.data; }
}
