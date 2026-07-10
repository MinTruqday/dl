import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibSpecialCharacter implements InlineTool {
  static get isInline() {
    return true;
  }

  private api: API;
  private button: HTMLButtonElement | null = null;

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = "S";
    return this.button;
  }

  surround(range: Range) {
    const char = prompt("Enter special character");
    if (char) {
      const textNode = document.createTextNode(char);
      range.insertNode(textNode);
    }
  }

  checkState(selection: Selection) {
    return false;
  }
}
