import { API } from "@editorjs/editorjs";

export default class DocLibGridlines {
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
    button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>';
    
    button.addEventListener("click", () => {
      button.classList.toggle(this.api.styles.settingsButtonActive);
    });
    
    this.api.tooltip.onHover(button, "Gridlines", { placement: "top" });
    return button;
  }

  save() {
    return {};
  }
}
