import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTitle implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { text: string };

  static get toolbox() {
    return {
      title: 'DocLib Title',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h8"></path><path d="M4 18V6"></path><path d="M12 18V6"></path><path d="M21 16h-4v-8h4"></path><path d="M17 12h4"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }
  static get enableLineBreaks() { return false; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
        text: data.text || ''
    };
  }

  render() {
    this.wrapper = document.createElement('h1');
    this.wrapper.classList.add(this.api.styles.block);
    this.wrapper.contentEditable = 'true';
    this.wrapper.innerHTML = this.data.text;
    this.wrapper.dataset.placeholder = 'Enter Main Title';
    
    this.wrapper.style.fontSize = '2.25rem';
    this.wrapper.style.fontWeight = '700';
    this.wrapper.style.lineHeight = '1.2';
    this.wrapper.style.margin = '24px 0 16px 0';
    this.wrapper.style.outline = 'none';

    this.wrapper.addEventListener('input', () => {
        this.data.text = this.wrapper!.innerHTML;
    });

    this.wrapper.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            this.api.blocks.insert();
            this.api.caret.setToBlock(this.api.blocks.getCurrentBlockIndex() + 1);
        }
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return {
      text: this.wrapper ? this.wrapper.innerHTML : this.data.text
    };
  }
  
  static get sanitize() {
      return {
          text: { br: true, b: true, i: true, a: true, span: true }
      };
  }
}
