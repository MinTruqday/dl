import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibButton implements BlockTool {
  static readonly feature = {
    id: "DocLibButton",
    title: "DocLib Button",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="085088b8d1ea9900"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="12,16 4,18 9,17 4,4 10,11 18,18"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private data: { link: string; text: string };
  private wrapper: HTMLElement | null = null;

  private container: HTMLElement | null = null;
  private inputHolder: HTMLElement | null = null;
  private anyButtonHolder: HTMLElement | null = null;
  private textInput: HTMLElement | null = null;
  private linkInput: HTMLElement | null = null;
  private registButton: HTMLButtonElement | null = null;
  private anyButton: HTMLAnchorElement | null = null;
  private readOnly: boolean;

  private CSS = {
    baseClass: "cdx-block",
    hide: "hide",
    btn: "anyButton__btn",
    container: "anyButtonContainer",
    input: "anyButtonContainer__input",
    inputHolder: "anyButtonContainer__inputHolder",
    inputText: "anyButtonContainer__input--text",
    inputLink: "anyButtonContainer__input--link",
    registButton: "anyButtonContainer__registerButton",
    anyButtonHolder: "anyButtonContainer__anyButtonHolder",
    btnColor: "anyButton__btn--default",
  };

  static get STATE() {
    return { EDIT: 0, VIEW: 1 };
  }

  static get toolbox() {
    return {
      title: "DocLib Button",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="085088b8d1ea9900"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="12,16 4,18 9,17 4,4 10,11 18,18"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }
  static get enableLineBreaks() {
    return false;
  }

  constructor({
    api,
    data,
    readOnly,
  }: {
    api: API;
    data: any;
    readOnly: boolean;
  }) {
    this.api = api;
    this.readOnly = readOnly;
    this.data = {
      link: data.link || "",
      text: data.text || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.CSS.baseClass);

    this.container = document.createElement("div");
    this.container.classList.add(this.CSS.container);

    this.inputHolder = this.makeInputHolder();
    this.anyButtonHolder = this.makeAnyButtonHolder();

    this.container.appendChild(this.inputHolder);
    this.container.appendChild(this.anyButtonHolder);

    if (this.data.link !== "") {
      this.init();
      this.show(DocLibButton.STATE.VIEW);
    }

    this.wrapper.appendChild(this.container);

    if (!document.getElementById("doclib-button-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-button-styles";
      style.innerHTML = `
            .anyButtonContainer__inputHolder { display: flex; flex-direction: column; gap: 10px; padding: 15px; border: 1px dashed hsl(var(--border)); border-radius: 5px; background: hsl(var(--surface-raised)); }
            .anyButtonContainer__registerButton { margin-top: 5px; background: hsl(var(--brand)); color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; }
            .anyButtonContainer__registerButton:hover { background: #0056b3; }
            .anyButton__btn { display: inline-block; padding: 10px 20px; border-radius: 5px; text-decoration: none; text-align: center; font-weight: bold; cursor: pointer; }
            .anyButton__btn--default { background: hsl(var(--brand)); color: white; }
            .anyButton__btn--default:hover { opacity: 0.9; }
            .hide { display: none !important; }
            .anyButtonContainer__anyButtonHolder { text-align: center; margin: 10px 0; }
        `;
      document.head.appendChild(style);
    }

    return this.wrapper;
  }

  makeInputHolder() {
    const inputHolder = document.createElement("div");
    inputHolder.classList.add(this.CSS.inputHolder);

    this.textInput = document.createElement("div");
    this.textInput.classList.add(
      this.api.styles.input,
      this.CSS.input,
      this.CSS.inputText,
    );
    this.textInput.contentEditable = (!this.readOnly).toString();
    this.textInput.dataset.placeholder = "DocLib Text";

    this.linkInput = document.createElement("div");
    this.linkInput.classList.add(
      this.api.styles.input,
      this.CSS.input,
      this.CSS.inputLink,
    );
    this.linkInput.contentEditable = (!this.readOnly).toString();
    this.linkInput.dataset.placeholder = "DocLib URL";

    this.registButton = document.createElement("button");
    this.registButton.classList.add(this.CSS.registButton);
    this.registButton.type = "button";
    this.registButton.textContent = "Set";

    this.registButton.addEventListener("click", () => {
      if (!this.linkInput?.textContent || !this.textInput?.textContent) {
        alert("A label and URL are required");
        return;
      }
      this.data = {
        link: this.linkInput.textContent,
        text: this.textInput.textContent,
      };
      this.show(DocLibButton.STATE.VIEW);
    });

    inputHolder.appendChild(this.textInput);
    inputHolder.appendChild(this.linkInput);
    inputHolder.appendChild(this.registButton);

    return inputHolder;
  }

  makeAnyButtonHolder() {
    const holder = document.createElement("div");
    holder.classList.add(this.CSS.hide, this.CSS.anyButtonHolder);

    this.anyButton = document.createElement("a");
    this.anyButton.classList.add(this.CSS.btn, this.CSS.btnColor);
    this.anyButton.target = "_blank";
    this.anyButton.rel = "nofollow noindex noreferrer";
    this.anyButton.textContent = "Default Button";

    holder.appendChild(this.anyButton);
    return holder;
  }

  init() {
    if (this.textInput && this.linkInput) {
      this.textInput.textContent = this.data.text;
      this.linkInput.textContent = this.data.link;
    }
  }

  show(state: number) {
    if (this.anyButton) {
      this.anyButton.textContent = this.data.text;
      this.anyButton.href = this.data.link;
    }
    this.changeState(state);
  }

  changeState(state: number) {
    if (!this.inputHolder || !this.anyButtonHolder) return;

    if (state === DocLibButton.STATE.EDIT) {
      this.inputHolder.classList.remove(this.CSS.hide);
      this.anyButtonHolder.classList.add(this.CSS.hide);
    } else {
      this.inputHolder.classList.add(this.CSS.hide);
      this.anyButtonHolder.classList.remove(this.CSS.hide);
    }
  }

  renderSettings() {
    return [
      {
        icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="085088b8d1ea9900"><rect x="3" y="3" width="18" height="18" rx="3"/><polyline points="12,16 4,18 9,17 4,4 10,11 18,18"/></svg>',
        label: "Edit Button",
        name: "edit_mode",
        onActivate: () => {
          if (this.linkInput && this.textInput) {
            this.data = {
              link: this.linkInput.textContent || "",
              text: this.textInput.textContent || "",
            };
          }
          this.show(DocLibButton.STATE.EDIT);
        },
      },
    ];
  }

  save() {
    return this.data;
  }

  static get sanitize() {
    return { text: false, link: false };
  }
}
