import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibAiText implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { prompt: string, response: string, status: 'idle' | 'generating' | 'done' };

  static get toolbox() {
    return {
      title: 'DocLib AI',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      prompt: data.prompt || '',
      response: data.response || '',
      status: data.status || 'idle'
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-ai-text-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-ai-text-styles';
        style.innerHTML = `
            .doclib-ai-wrapper { border: 1px solid #e2e8f0; border-radius: 12px; background: linear-gradient(180deg, #f8fafc 0%, #fff 100%); margin: 16px 0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
            .doclib-ai-header { padding: 12px 16px; background: #eff6ff; border-bottom: 1px solid #bfdbfe; display: flex; align-items: center; gap: 8px; color: #1e3a8a; font-weight: 600; }
            .doclib-ai-icon { color: #3b82f6; }
            .doclib-ai-prompt { padding: 16px; display: flex; gap: 8px; border-bottom: 1px solid #e2e8f0; }
            .doclib-ai-input { flex-grow: 1; border: 1px solid #cbd5e1; padding: 8px 12px; border-radius: 6px; outline: none; transition: border 0.2s; font-size: 14px; }
            .doclib-ai-input:focus { border-color: #3b82f6; }
            .doclib-ai-btn { background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; transition: background 0.2s; }
            .doclib-ai-btn:hover { background: #2563eb; }
            .doclib-ai-btn:disabled { background: #94a3b8; cursor: not-allowed; }
            .doclib-ai-response { padding: 16px; min-height: 100px; font-size: 15px; line-height: 1.6; color: #334155; white-space: pre-wrap; outline: none; }
            .doclib-ai-generating { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; color: #94a3b8; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
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
      container.classList.add('doclib-ai-wrapper');
      
      const header = document.createElement('div');
      header.classList.add('doclib-ai-header');
      header.innerHTML = `
          <svg class="doclib-ai-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"></path><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
          DocLib AI Assistant
      `;
      container.appendChild(header);
      
      if (!this.api.readOnly.toggle && this.data.status !== 'done') {
          const promptRow = document.createElement('div');
          promptRow.classList.add('doclib-ai-prompt');
          
          const input = document.createElement('input');
          input.classList.add('doclib-ai-input');
          input.placeholder = 'Bạn muốn tôi viết gì? (VD: Viết một đoạn văn tóm tắt...)';
          input.value = this.data.prompt;
          
          const btn = document.createElement('button');
          btn.classList.add('doclib-ai-btn');
          btn.innerText = 'Tạo nội dung';
          
          if (this.data.status === 'generating') {
              input.disabled = true;
              btn.disabled = true;
              btn.innerText = 'Đang viết...';
          }
          
          const submit = () => {
              if (!input.value.trim() || this.data.status === 'generating') return;
              this.data.prompt = input.value;
              this.data.status = 'generating';
              this.buildUI();
              
              // Simulate API call
              setTimeout(() => {
                  this.data.response = "Dưới đây là nội dung AI đã tạo theo yêu cầu:\\n\\n" + this.data.prompt + "\\n\\nBạn có thể chỉnh sửa trực tiếp đoạn văn bản này để hoàn thiện nội dung. (Tính năng này đang được mock kết quả, vui lòng kết nối API backend thực tế để AI hoạt động).";
                  this.data.status = 'done';
                  this.buildUI();
              }, 2000);
          };
          
          btn.addEventListener('click', submit);
          input.addEventListener('keydown', (e) => {
              if (e.key === 'Enter') submit();
          });
          
          promptRow.appendChild(input);
          promptRow.appendChild(btn);
          container.appendChild(promptRow);
      }
      
      const responseBox = document.createElement('div');
      responseBox.classList.add('doclib-ai-response');
      responseBox.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
      
      if (this.data.status === 'generating') {
          responseBox.classList.add('doclib-ai-generating');
          responseBox.innerText = 'DocLib AI đang suy nghĩ và soạn thảo nội dung...';
          responseBox.contentEditable = 'false';
      } else if (this.data.status === 'done') {
          responseBox.innerText = this.data.response;
          responseBox.addEventListener('input', () => this.data.response = responseBox.innerText);
      } else {
          responseBox.style.display = 'none';
      }
      
      container.appendChild(responseBox);
      this.wrapper.appendChild(container);
  }

  save() { return this.data; }
}
