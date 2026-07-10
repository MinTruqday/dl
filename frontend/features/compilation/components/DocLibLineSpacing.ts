import { API } from "@editorjs/editorjs";

export default class DocLibLineSpacing {
  static get isTune() {
    return true;
  }

  private api: API;
  private data: { spacing: string };

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { spacing: data.spacing || "1.0" };
  }

  render() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("doclib-line-spacing");
    
    const spaces = ["1.0", "1.5", "2.0"];
    spaces.forEach(space => {
      const btn = document.createElement("button");
      btn.innerText = space;
      btn.addEventListener("click", () => {
        this.data.spacing = space;
      });
      wrapper.appendChild(btn);
    });

    return wrapper;
  }

  save() {
    return this.data;
  }
}
