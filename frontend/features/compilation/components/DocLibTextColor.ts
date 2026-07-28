import { API, InlineTool } from "@editorjs/editorjs";

interface DocLibColorConfig {
  defaultColor?: string;
  type?: "text" | "marker";
  colorCollections?: string[];
  customPicker?: boolean;
}

export default class DocLibColorPicker implements InlineTool {
  static readonly feature = {
    id: "DocLibTextColor",
    title: "DocLib TextColor",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="1cb639a4ace6b4f5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="15,16 10,15 6,13 14,11 18,11 10,8"/></svg>',
    origin: "doclib-native",
  } as const;

  static get isInline() {
    return true;
  }

  static get title() {
    return "DocLib Text Color";
  }

  static get sanitize() {
    return {
      span: { class: true, style: { color: true, "background-color": true } },
    };
  }

  private api: API;
  private config: DocLibColorConfig;
  private button: HTMLButtonElement | null = null;
  private pluginType: "text" | "marker";
  private parentClass: string;
  private hasCustomPicker: boolean;
  private colorCollections: string[];
  private _state: boolean = false;
  private lastRange: Range | null = null;

  constructor({ api, config }: { api: API; config?: DocLibColorConfig }) {
    this.api = api;
    this.config = config || {};
    this.pluginType = this.config.type || "text";
    this.parentClass = "cdx-text-color";
    this.hasCustomPicker = this.config.customPicker !== false;
    this.colorCollections = this.config.colorCollections || [
      "#FF1300",
      "#EC7878",
      "#9C27B0",
      "#673AB7",
      "#3F51B5",
      "#0070FF",
      "#03A9F4",
      "#00BCD4",
      "#4CAF50",
      "#8BC34A",
      "#CDDC39",
      "#FFE500",
      "#FFBF00",
      "#FF9800",
      "#795548",
      "#9E9E9E",
      "#5A5A5A",
      "#FFF",
    ];
  }

  render() {
    this.button = document.createElement("button");
    (this.button as HTMLButtonElement).type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = this.getIcon();

    this.button.addEventListener("mousedown", (e) => {
      e.preventDefault();
    });

    return this.button;
  }

  private getIcon() {
    if (this.pluginType === "marker") {
      return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="1cb639a4ace6b4f5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="15,16 10,15 6,13 14,11 18,11 10,8"/></svg>';
    } else {
      return '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="1cb639a4ace6b4f5"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="15,16 10,15 6,13 14,11 18,11 10,8"/></svg>';
    }
  }

  surround(range: Range | null) {
    this.lastRange = range;
    if (this._state) {
      const parent = this.api.selection.findParentTag("SPAN", this.parentClass);
      if (parent) {
        const text = document.createTextNode(parent.textContent || "");
        parent.parentNode?.replaceChild(text, parent);
      }
    }
  }

  checkState() {
    const parentNode = this.api.selection.findParentTag(
      "SPAN",
      this.parentClass,
    );
    this._state = !!parentNode;
    if (this.button) {
      this.button.classList.toggle(
        this.api.styles.inlineToolButtonActive,
        this._state,
      );
    }
    return this._state;
  }

  renderActions(): HTMLElement {
    const container = document.createElement("div");
    container.style.display = "grid";
    container.style.gap = "10px";
    container.style.padding = "4px";
    container.style.gridTemplateColumns = "repeat(7, 1fr)";

    this.colorCollections.forEach((colorValue) => {
      const colorItem = document.createElement("div");
      colorItem.style.width = "30px";
      colorItem.style.height = "30px";
      colorItem.style.display = "block";
      colorItem.style.cursor = "pointer";
      colorItem.style.borderRadius = "100%";
      colorItem.style.transition = "transform 0.2s ease";
      colorItem.style.backgroundColor = colorValue;

      colorItem.onmouseenter = () => {
        colorItem.style.transform = "scale(1.1)";
      };
      colorItem.onmouseleave = () => {
        colorItem.style.transform = "scale(1)";
      };

      colorItem.onclick = () => {
        this.applyColor(this.lastRange, colorValue);
      };

      container.appendChild(colorItem);
    });

    if (this.hasCustomPicker) {
      const customBtn = document.createElement("div");
      customBtn.style.width = "30px";
      customBtn.style.height = "30px";
      customBtn.style.display = "block";
      customBtn.style.cursor = "pointer";
      customBtn.style.borderRadius = "100%";
      customBtn.style.transition = "transform 0.2s ease";
      customBtn.style.background =
        "conic-gradient(red, yellow, lime, aqua, blue, magenta, red)";

      customBtn.onmouseenter = () => {
        customBtn.style.transform = "scale(1.1)";
      };
      customBtn.onmouseleave = () => {
        customBtn.style.transform = "scale(1)";
      };

      const nativeColorInput = document.createElement("input");
      nativeColorInput.type = "color";
      nativeColorInput.style.position = "absolute";
      nativeColorInput.style.opacity = "0";
      nativeColorInput.style.width = "0";
      nativeColorInput.style.height = "0";
      nativeColorInput.addEventListener("input", (e: any) => {
        this.applyColor(this.lastRange, e.target.value);
      });

      customBtn.addEventListener("click", () => {
        nativeColorInput.click();
      });

      container.appendChild(customBtn);
      container.appendChild(nativeColorInput);
    }

    return container;
  }

  private applyColor(range: Range | null, color: string) {
    if (!range) return;

    const selectedText = range.extractContents();
    const span = document.createElement("span");
    span.classList.add(this.parentClass);
    span.appendChild(selectedText);

    if (this.pluginType === "marker") {
      span.style.backgroundColor = color;
    } else {
      span.style.color = color;
    }

    span.innerHTML = span.textContent || "";
    range.insertNode(span);
    this.api.selection.expandToTag(span);
    this.api.inlineToolbar.close();
  }

  clear() {
    this.button = null;
  }
}
