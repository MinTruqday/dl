import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTable implements BlockTool {
  private api: API;
  private data: { content: string[][] };
  private wrapper: HTMLElement | null = null;
  private tbody: HTMLElement | null = null;

  static get toolbox() {
    return {
      title: 'DocLib Table',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="3" y1="15" x2="21" y2="15"></line><line x1="9" y1="9" x2="9" y2="21"></line><line x1="15" y1="9" x2="15" y2="21"></line></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      content: (data.content && data.content.length > 0) ? data.content : [
        ['', ''],
        ['', '']
      ]
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById('doclib-table-styles')) {
      const style = document.createElement('style');
      style.id = 'doclib-table-styles';
      style.innerHTML = `
        .doclib-table-wrapper { width: 100%; margin: 16px 0; overflow-x: auto; }
        .doclib-table { width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; }
        .doclib-table td { border: 1px solid #e2e8f0; padding: 8px 12px; min-width: 100px; outline: none; }
        .doclib-table td:empty::before { content: ''; color: #cbd5e1; }
        .doclib-table-controls { display: flex; gap: 8px; margin-top: 8px; justify-content: flex-end; }
        .doclib-table-btn { padding: 4px 8px; font-size: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; cursor: pointer; color: #475569; }
        .doclib-table-btn:hover { background: #e2e8f0; }
      `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add('doclib-table-wrapper');
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = '';

    const table = document.createElement('table');
    table.classList.add('doclib-table');
    this.tbody = document.createElement('tbody');

    this.data.content.forEach(rowData => {
      const tr = document.createElement('tr');
      rowData.forEach(cellData => {
        const td = document.createElement('td');
        td.contentEditable = 'true';
        td.innerHTML = cellData;
        td.addEventListener('input', () => this.saveData());
        tr.appendChild(td);
      });
      this.tbody!.appendChild(tr);
    });

    table.appendChild(this.tbody);
    this.wrapper.appendChild(table);

    const controls = document.createElement('div');
    controls.classList.add('doclib-table-controls');

    const addRowBtn = document.createElement('button');
    addRowBtn.classList.add('doclib-table-btn');
    addRowBtn.innerText = '+ Add row';
    addRowBtn.addEventListener('click', () => {
      const cols = this.data.content[0]?.length || 2;
      this.data.content.push(Array(cols).fill(''));
      this.buildUI();
    });

    const addColBtn = document.createElement('button');
    addColBtn.classList.add('doclib-table-btn');
    addColBtn.innerText = '+ Add column';
    addColBtn.addEventListener('click', () => {
      this.data.content.forEach(row => row.push(''));
      this.buildUI();
    });
    
    const rmRowBtn = document.createElement('button');
    rmRowBtn.classList.add('doclib-table-btn');
    rmRowBtn.innerText = '- Remove row';
    rmRowBtn.addEventListener('click', () => {
      if (this.data.content.length > 1) {
          this.data.content.pop();
          this.buildUI();
      }
    });
    
    const rmColBtn = document.createElement('button');
    rmColBtn.classList.add('doclib-table-btn');
    rmColBtn.innerText = '- Remove column';
    rmColBtn.addEventListener('click', () => {
      if (this.data.content[0]?.length > 1) {
          this.data.content.forEach(row => row.pop());
          this.buildUI();
      }
    });

    controls.appendChild(addRowBtn);
    controls.appendChild(addColBtn);
    controls.appendChild(rmRowBtn);
    controls.appendChild(rmColBtn);
    this.wrapper.appendChild(controls);
  }

  private saveData() {
    if (!this.tbody) return;
    const rows = Array.from(this.tbody.querySelectorAll('tr'));
    this.data.content = rows.map(tr => {
      return Array.from(tr.querySelectorAll('td')).map(td => td.innerHTML);
    });
  }

  save() {
    this.saveData();
    return this.data;
  }
}
