import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibPoll implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { question: string, options: { text: string, votes: number }[] };

  static get toolbox() {
    return {
      title: 'DocLib Poll',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      question: data.question || '',
      options: data.options && data.options.length > 0 ? data.options : [
          { text: 'Option 1', votes: 0 },
          { text: 'Option 2', votes: 0 }
      ]
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-poll-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-poll-styles';
        style.innerHTML = `
            .doclib-po-wrapper { border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin: 16px 0; background: #fff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
            .doclib-po-question { font-size: 1.2em; font-weight: 700; color: #0f172a; margin-bottom: 16px; outline: none; }
            .doclib-po-question:empty::before { content: 'Enter survey question'; color: #94a3b8; }
            .doclib-po-options { display: flex; flex-direction: column; gap: 12px; }
            .doclib-po-option { display: flex; align-items: center; gap: 12px; }
            .doclib-po-bar-wrapper { flex-grow: 1; height: 40px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; position: relative; overflow: hidden; display: flex; align-items: center; cursor: pointer; transition: border-color 0.2s; }
            .doclib-po-bar-wrapper:hover { border-color: #cbd5e1; }
            .doclib-po-bar-fill { position: absolute; left: 0; top: 0; bottom: 0; background: #eff6ff; z-index: 1; transition: width 0.3s ease-out; border-right: 2px solid #3b82f6; }
            .doclib-po-text { position: relative; z-index: 2; margin-left: 12px; font-weight: 500; color: #334155; outline: none; flex-grow: 1; }
            .doclib-po-text:empty::before { content: 'Enter option'; color: #94a3b8; }
            .doclib-po-pct { position: relative; z-index: 2; margin-right: 12px; font-weight: 600; color: #3b82f6; font-size: 13px; }
            .doclib-po-rm { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; background: #fee2e2; color: #ef4444; border: none; border-radius: 4px; cursor: pointer; flex-shrink: 0; }
            .doclib-po-add { margin-top: 16px; width: 100%; padding: 10px; background: transparent; border: 1px dashed #cbd5e1; border-radius: 6px; color: #64748b; font-weight: 500; cursor: pointer; }
            .doclib-po-add:hover { background: #f8fafc; }
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
      container.classList.add('doclib-po-wrapper');
      
      const question = document.createElement('div');
      question.classList.add('doclib-po-question');
      question.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
      question.innerHTML = this.data.question;
      question.addEventListener('input', () => this.data.question = question.innerHTML);
      container.appendChild(question);
      
      const optionsDiv = document.createElement('div');
      optionsDiv.classList.add('doclib-po-options');
      
      let totalVotes = this.data.options.reduce((sum, opt) => sum + opt.votes, 0);
      if (totalVotes === 0) totalVotes = 1; 
      
      this.data.options.forEach((opt, index) => {
          const optEl = document.createElement('div');
          optEl.classList.add('doclib-po-option');
          
          const barWrap = document.createElement('div');
          barWrap.classList.add('doclib-po-bar-wrapper');
          
          const fill = document.createElement('div');
          fill.classList.add('doclib-po-bar-fill');
          const pctVal = Math.round((opt.votes / totalVotes) * 100);
          fill.style.width = `${totalVotes === 1 && opt.votes === 0 ? 0 : pctVal}%`;
          
          const text = document.createElement('div');
          text.classList.add('doclib-po-text');
          text.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
          text.innerHTML = opt.text;
          text.addEventListener('input', () => opt.text = text.innerHTML);
          
          const pct = document.createElement('div');
          pct.classList.add('doclib-po-pct');
          pct.innerText = `${totalVotes === 1 && opt.votes === 0 ? 0 : pctVal}% (${opt.votes})`;
          
          barWrap.appendChild(fill);
          barWrap.appendChild(text);
          barWrap.appendChild(pct);
          
          
          barWrap.addEventListener('click', (e) => {
              if (e.target === text && !this.api.readOnly.toggle) return; 
              opt.votes++;
              this.buildUI();
          });
          
          optEl.appendChild(barWrap);
          
          if (!this.api.readOnly.toggle && this.data.options.length > 2) {
              const rmBtn = document.createElement('button');
              rmBtn.classList.add('doclib-po-rm');
              rmBtn.innerHTML = '&times;';
              rmBtn.addEventListener('click', () => {
                  this.data.options.splice(index, 1);
                  this.buildUI();
              });
              optEl.appendChild(rmBtn);
          }
          
          optionsDiv.appendChild(optEl);
      });
      
      container.appendChild(optionsDiv);
      
      if (!this.api.readOnly.toggle) {
          const addBtn = document.createElement('button');
          addBtn.classList.add('doclib-po-add');
          addBtn.innerText = '+ Add Option';
          addBtn.addEventListener('click', () => {
              this.data.options.push({ text: '', votes: 0 });
              this.buildUI();
          });
          container.appendChild(addBtn);
      }
      
      this.wrapper.appendChild(container);
  }

  save() { return this.data; }
}
