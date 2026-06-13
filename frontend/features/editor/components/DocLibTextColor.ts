import { API, InlineTool } from "@editorjs/editorjs";

interface DocLibColorConfig {
  defaultColor?: string;
  type?: "text" | "marker";
  colorCollections?: string[];
  customPicker?: boolean;
}

export default class DocLibColorPicker implements InlineTool {
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
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = this.getIcon();

    this.button.addEventListener("mousedown", (e) => {
      e.preventDefault();
    });

    return this.button;
  }

  private getIcon() {
    if (this.pluginType === "marker") {
      return '<svg fill="#000000" height="20px" width="20px" version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 491.644 491.644"><path d="M456.623,2.282c-42.758-20.283-141.107,96.84-223.473,264.224c-2.35,4.776-2.686,10.294-0.936,15.32c1.75,5.026,5.442,9.145,10.251,11.426L366.758,352.2c4.809,2.281,10.332,2.538,15.333,0.714c5.001-1.825,9.059-5.579,11.272-10.42C470.883,172.829,499.385,22.562,456.623,2.282z"/><path d="M34.71,461.799l-17.257,16.708c-2.225,2.17-2.934,5.475-1.773,8.363c1.179,2.886,3.985,4.773,7.099,4.773h160.887c-1.364-5.043-0.921-10.445,1.391-15.306l7.919-16.692H40.036C38.036,459.646,36.129,460.419,34.71,461.799z"/><path d="M264.766,448.864l-32.615-15.458c-1.046-0.502-2.161-0.744-3.257-0.744c-2.87,0-5.611,1.614-6.901,4.372l-22.001,46.384c-0.871,1.789-0.723,3.895,0.341,5.564c1.046,1.661,2.888,2.661,4.855,2.661h0.046l44.275-0.378c2.206-0.016,4.206-1.299,5.159-3.292l13.724-28.925c0.856-1.838,0.967-3.936,0.29-5.846C268.004,451.292,266.585,449.728,264.766,448.864z"/><path d="M348.445,366.038l-112.572-51.392c-8.909-4.067-19.434-0.227-23.63,8.622c-2.551,5.378-3.58,11.353-2.975,17.275l5.2,50.909c0.703,6.882,4.983,12.884,11.261,15.792l60.031,27.797c6.688,3.097,14.548,2.179,20.343-2.375l45.983-36.137c4.931-3.875,7.487-10.041,6.743-16.269C358.086,374.032,354.151,368.642,348.445,366.038z"/></svg>';
    } else {
      return '<svg fill="#000000" height="20px" width="20px" viewBox="-6 0 512 512" xmlns="http://www.w3.org/2000/svg"><path d="M365 432L328 352 172 352 135 432 64 432 227 80 272 80 436 432 365 432ZM201 288L299 288 250 183 201 288Z"></path></svg>';
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
