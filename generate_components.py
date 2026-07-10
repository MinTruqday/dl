import os

DIR = "frontend/features/compilation/components"
os.makedirs(DIR, exist_ok=True)

components = {}

components["DocLibIcons.ts"] = """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibIcons implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { iconName: string };

  static get toolbox() {
    return {
      title: "DocLib Icons",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 22h20L12 2z"></path></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { iconName: data.iconName || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-icons");
    const input = document.createElement("input");
    input.placeholder = "Enter icon name";
    input.value = this.data.iconName;
    input.addEventListener("input", (e) => {
      this.data.iconName = (e.target as HTMLInputElement).value;
    });
    this.wrapper.appendChild(input);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("input");
    return {
      iconName: input ? input.value : "",
    };
  }
}
"""

components["DocLib3DModels.ts"] = """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLib3DModels implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { modelUrl: string };

  static get toolbox() {
    return {
      title: "DocLib 3D Models",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><box></box></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { modelUrl: data.modelUrl || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-3d-models");
    const input = document.createElement("input");
    input.placeholder = "Enter GLTF model URL";
    input.value = this.data.modelUrl;
    input.addEventListener("input", (e) => {
      this.data.modelUrl = (e.target as HTMLInputElement).value;
    });
    this.wrapper.appendChild(input);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("input");
    return {
      modelUrl: input ? input.value : "",
    };
  }
}
"""

components["DocLibSpecialCharacter.ts"] = """import { API, InlineTool } from "@editorjs/editorjs";

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
"""

components["DocLibEndnote.ts"] = """import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibEndnote implements InlineTool {
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
    this.button.innerHTML = "EN";
    return this.button;
  }

  surround(range: Range) {
    const wrapper = document.createElement("sup");
    wrapper.classList.add("doclib-endnote-marker");
    const id = Math.random().toString(36).substring(2, 9);
    wrapper.dataset.endnoteId = id;
    wrapper.innerText = "E";
    range.surroundContents(wrapper);
  }

  checkState() {
    return false;
  }
}
"""

components["DocLibPageSetup.ts"] = """import { API } from "@editorjs/editorjs";

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
"""

components["DocLibLineSpacing.ts"] = """import { API } from "@editorjs/editorjs";

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
"""

components["DocLibDictation.ts"] = """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibDictation implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { text: string };

  static get toolbox() {
    return {
      title: "DocLib Dictation",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { text: data.text || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-dictation");
    
    const btn = document.createElement("button");
    btn.innerText = "Start Dictation";
    
    const textArea = document.createElement("textarea");
    textArea.value = this.data.text;
    textArea.addEventListener("input", (e) => {
      this.data.text = (e.target as HTMLTextAreaElement).value;
    });

    this.wrapper.appendChild(btn);
    this.wrapper.appendChild(textArea);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("textarea");
    return {
      text: input ? input.value : "",
    };
  }
}
"""

components["DocLibFormatPainter.ts"] = """import { API, InlineTool } from "@editorjs/editorjs";

export default class DocLibFormatPainter implements InlineTool {
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
    this.button.innerHTML = "FP";
    return this.button;
  }

  surround(range: Range) {
    const wrapper = document.createElement("span");
    wrapper.classList.add("doclib-format-painter-target");
    range.surroundContents(wrapper);
  }

  checkState() {
    return false;
  }
}
"""

components["DocLibScreenClipping.ts"] = """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibScreenClipping implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { imageData: string };

  static get toolbox() {
    return {
      title: "DocLib Screen Clipping",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { imageData: data.imageData || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-screen-clipping");
    
    const btn = document.createElement("button");
    btn.innerText = "Take Screenshot";
    
    const img = document.createElement("img");
    img.src = this.data.imageData;

    this.wrapper.appendChild(btn);
    this.wrapper.appendChild(img);
    return this.wrapper;
  }

  save() {
    return {
      imageData: this.data.imageData,
    };
  }
}
"""

components["DocLibLabels.ts"] = """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibLabels implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { labelType: string };

  static get toolbox() {
    return {
      title: "DocLib Labels",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>',
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { labelType: data.labelType || "Avery" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-labels");
    const input = document.createElement("input");
    input.placeholder = "Enter label type";
    input.value = this.data.labelType;
    input.addEventListener("input", (e) => {
      this.data.labelType = (e.target as HTMLInputElement).value;
    });
    this.wrapper.appendChild(input);
    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    const input = blockContent.querySelector("input");
    return {
      labelType: input ? input.value : "",
    };
  }
}
"""

for filename, content in components.items():
    with open(f"{DIR}/{filename}", "w") as f:
        f.write(content)

print("Created 10 component files.")
