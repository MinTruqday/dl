import os

DIR = "frontend/features/compilation/components"
os.makedirs(DIR, exist_ok=True)

components = {
    "DocLibTabStops": """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibTabStops implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { stops: string };

  static get toolbox() {
    return {
      title: "DocLib Tab Stops",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12h16M4 6h16M4 18h16"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { stops: data.stops || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-tab-stops");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.stops;
    this.wrapper.dataset.placeholder = "Set tab stops";

    this.wrapper.addEventListener("input", () => {
      this.data.stops = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { stops: blockContent.innerHTML };
  }
}
""",
    "DocLibField": """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibField implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { code: string };

  static get toolbox() {
    return {
      title: "DocLib Field Code",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { code: data.code || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-field");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.code;
    this.wrapper.dataset.placeholder = "Insert field code";

    this.wrapper.addEventListener("input", () => {
      this.data.code = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { code: blockContent.innerHTML };
  }
}
""",
    "DocLibSparklines": """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibSparklines implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { values: string };

  static get toolbox() {
    return {
      title: "DocLib Sparklines",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18M7 14l5-5 4 4 5-5"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { values: data.values || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-sparklines");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.values;
    this.wrapper.dataset.placeholder = "Sparkline data";

    this.wrapper.addEventListener("input", () => {
      this.data.values = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { values: blockContent.innerHTML };
  }
}
""",
    "DocLibOleObject": """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibOleObject implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { objectId: string };

  static get toolbox() {
    return {
      title: "DocLib OLE Object",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { objectId: data.objectId || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-ole-object");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.objectId;
    this.wrapper.dataset.placeholder = "OLE Object ID";

    this.wrapper.addEventListener("input", () => {
      this.data.objectId = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { objectId: blockContent.innerHTML };
  }
}
""",
    "DocLibTextEffects": """import { API } from "@editorjs/editorjs";

export default class DocLibTextEffects {
  private api: API;
  private button: HTMLElement | null = null;
  private _state: boolean = false;

  static get isInline() {
    return true;
  }

  get state() {
    return this._state;
  }

  set state(state) {
    this._state = state;
    if (this.button) {
      this.button.classList.toggle(this.api.styles.inlineToolButtonActive, state);
    }
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7V4h16v3M9 20h6M12 4v16"/></svg>';
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    const wrapper = document.createElement("span");
    wrapper.classList.add("doclib-text-effects");
    wrapper.appendChild(range.extractContents());
    range.insertNode(wrapper);
    this.api.selection.expandToTag(wrapper);
  }

  checkState(selection: Selection) {
    const text = selection.anchorNode;
    if (!text) return;
    const anchorElement = text instanceof Element ? text : text.parentElement;
    if (anchorElement) {
      this.state = !!anchorElement.closest(".doclib-text-effects");
    }
  }
}
""",
    "DocLibReadAloud": """import { API } from "@editorjs/editorjs";

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
    
    this.api.tooltip.onHover(button, "DocLib Read Aloud", { placement: "top" });
    return button;
  }

  save() {
    return {};
  }
}
""",
    "DocLibFocusMode": """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibFocusMode implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { focus: string };

  static get toolbox() {
    return {
      title: "DocLib Focus Mode",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { focus: data.focus || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-focus-mode");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.focus;
    this.wrapper.dataset.placeholder = "Focus content";

    this.wrapper.addEventListener("input", () => {
      this.data.focus = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { focus: blockContent.innerHTML };
  }
}
""",
    "DocLibPhoneticGuide": """import { API } from "@editorjs/editorjs";

export default class DocLibPhoneticGuide {
  private api: API;
  private button: HTMLElement | null = null;
  private _state: boolean = false;

  static get isInline() {
    return true;
  }

  get state() {
    return this._state;
  }

  set state(state) {
    this._state = state;
    if (this.button) {
      this.button.classList.toggle(this.api.styles.inlineToolButtonActive, state);
    }
  }

  constructor({ api }: { api: API }) {
    this.api = api;
  }

  render() {
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19h16M4 5h16M12 5v14"/></svg>';
    return this.button;
  }

  surround(range: Range) {
    if (!range) return;
    const wrapper = document.createElement("ruby");
    wrapper.classList.add("doclib-phonetic");
    wrapper.appendChild(range.extractContents());
    const rt = document.createElement("rt");
    rt.textContent = "phonetic";
    wrapper.appendChild(rt);
    range.insertNode(wrapper);
    this.api.selection.expandToTag(wrapper);
  }

  checkState(selection: Selection) {
    const text = selection.anchorNode;
    if (!text) return;
    const anchorElement = text instanceof Element ? text : text.parentElement;
    if (anchorElement) {
      this.state = !!anchorElement.closest("ruby.doclib-phonetic");
    }
  }
}
""",
    "DocLibGridlines": """import { API } from "@editorjs/editorjs";

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
    
    this.api.tooltip.onHover(button, "DocLib Gridlines", { placement: "top" });
    return button;
  }

  save() {
    return {};
  }
}
""",
    "DocLibAccessibilityChecker": """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibAccessibilityChecker implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { result: string };

  static get toolbox() {
    return {
      title: "DocLib Accessibility",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="16" cy="4" r="1"/><path d="m18 19 1-7-6 1"/><path d="m5 8 3-3 5.5 3-2.36 3.5"/><path d="M4.24 14.5a5 5 0 0 0 6.88 6"/><path d="M13.76 17.5a5 5 0 0 0-6.88-6"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { result: data.result || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-accessibility");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.result;
    this.wrapper.dataset.placeholder = "Accessibility status";

    this.wrapper.addEventListener("input", () => {
      this.data.result = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { result: blockContent.innerHTML };
  }
}
""",
    "DocLibRestrictEditing": """import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibRestrictEditing implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { content: string };

  static get toolbox() {
    return {
      title: "DocLib Restrict Editing",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
    };
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = { content: data.content || "" };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block, "doclib-restrict");
    this.wrapper.contentEditable = "true";
    this.wrapper.innerHTML = this.data.content;
    this.wrapper.dataset.placeholder = "Restricted content";

    this.wrapper.addEventListener("input", () => {
      this.data.content = this.wrapper!.innerHTML;
    });

    return this.wrapper;
  }

  save(blockContent: HTMLElement) {
    return { content: blockContent.innerHTML };
  }
}
"""
}

for name, content in components.items():
    with open(os.path.join(DIR, f"{name}.ts"), "w") as f:
        f.write(content)

print("Generated 11 new components successfully.")
