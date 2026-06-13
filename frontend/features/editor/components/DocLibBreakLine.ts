import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibBreakLine implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: any;

  static get toolbox() {
    return {
      title: 'DocLib Break Line',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = data || {};
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-breakline-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-breakline-styles';
        style.innerHTML = `
            .doclib-breakline { margin: 24px 0; border: none; border-top: 1px solid #e2e8f0; }
        `;
        document.head.appendChild(style);
    }

    const hr = document.createElement('hr');
    hr.classList.add('doclib-breakline');
    this.wrapper.appendChild(hr);

    return this.wrapper;
  }

  save() {
    return {};
  }
}
