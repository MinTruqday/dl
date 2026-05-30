import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibChangeCase implements InlineTool {
  private api: API;
  private button: HTMLButtonElement | null = null;
  private _state: boolean = false;

  static get isInline() { return true; }
  static get title() { return "DocLib Change Case"; }
  
  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h4M12 20h8M6.9 15h6.2M10 4l-5 16M21 20l-5-16M16 4l-1 3"></path></svg>';
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;

    const selectedText = range.toString();
    if (!selectedText) return;

    let newText = '';
    
    // Cycle logic: original -> UPPER -> lower -> Title
    if (selectedText === selectedText.toUpperCase()) {
        newText = selectedText.toLowerCase();
    } else if (selectedText === selectedText.toLowerCase()) {
        newText = selectedText.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substring(1).toLowerCase());
    } else {
        newText = selectedText.toUpperCase();
    }

    range.deleteContents();
    range.insertNode(document.createTextNode(newText));
    
    this.api.selection.expandToTag(document.createElement('span')); 
    this.api.inlineToolbar.close();
  }

  checkState() {
    return false;
  }
}
