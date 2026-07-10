import { API } from "@editorjs/editorjs";

export default class DocLibReadAloud {
  private api: API;

  static get isTune() {
    return true;
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    const button = document.createElement("div");
    button.classList.add(this.api.styles.settingsButton);
    button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/></svg>';
    
    button.addEventListener("click", () => {
      button.classList.toggle(this.api.styles.settingsButtonActive);
    });
    
    this.api.tooltip.onHover(button, "Read Aloud", { placement: "top" });
    return button;
  }

  save() {
    return {};
  }
}
