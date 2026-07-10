import { API } from "@editorjs/editorjs";

export default class DocLibPageSetup {
  static get isTune() {
    return true;
  }

  private api: API;
  private data: { orientation: string };

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { orientation: data.orientation || "portrait" };
  }

  render() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("doclib-page-setup");
    
    const portraitBtn = document.createElement("button");
    portraitBtn.innerText = "Portrait";
    portraitBtn.addEventListener("click", () => {
      this.data.orientation = "portrait";
    });

    const landscapeBtn = document.createElement("button");
    landscapeBtn.innerText = "Landscape";
    landscapeBtn.addEventListener("click", () => {
      this.data.orientation = "landscape";
    });

    wrapper.appendChild(portraitBtn);
    wrapper.appendChild(landscapeBtn);
    return wrapper;
  }

  save() {
    return this.data;
  }
}
