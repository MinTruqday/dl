import { API, BlockTune } from "@editorjs/editorjs";

export default class DocLibNotice implements BlockTune {
  private api: API;
  private data: { style: string | undefined; caption: string };
  private block: any;
  private input: HTMLInputElement;
  private wrapper: HTMLElement | null = null;
  private tunes = [
    {
      name: "info",
      icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>',
      title: "Info",
    },
    {
      name: "warning",
      icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
      title: "Warning",
    },
    {
      name: "spoiler",
      icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>',
      title: "Spoiler",
    },
  ];

  static get isTune() {
    return true;
  }

  constructor({ api, data, block }: { api: API; data: any; block: any }) {
    this.api = api;
    this.data = {
      style: data?.style || undefined,
      caption: data?.caption || "",
    };
    this.block = block;

    this.input = document.createElement("input");
    this.input.classList.add(this.api.styles.input, "doclib-notice-input");
    this.input.placeholder = "Enter notice title";
    this.input.value = this.data.caption;

    this.input.addEventListener("input", () => {
      this.data.caption = this.input.value;
      this.block.dispatchChange();
    });
  }

  render() {
    const tuneWrapper = document.createElement("div");

    this.tunes.forEach((tune) => {
      const btn = document.createElement("div");
      btn.classList.add(this.api.styles.settingsButton);
      btn.innerHTML = tune.icon;
      if (this.data.style === tune.name)
        btn.classList.add(this.api.styles.settingsButtonActive);

      this.api.tooltip.onHover(btn, tune.title, {
        placement: "top",
        hidingDelay: 500,
      });

      btn.addEventListener("click", () => {
        const isActive = btn.classList.contains(
          this.api.styles.settingsButtonActive,
        );
        Array.from(tuneWrapper.children).forEach((b) =>
          b.classList.remove(this.api.styles.settingsButtonActive),
        );

        if (!isActive) {
          btn.classList.add(this.api.styles.settingsButtonActive);
          this.applyStyle(tune.name);
        } else {
          this.applyStyle(undefined);
        }
        this.block.dispatchChange();
      });

      tuneWrapper.appendChild(btn);
    });

    if (!document.getElementById("doclib-notice-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-notice-styles";
      style.innerHTML = `
            .doclib-notice-input { margin-bottom: 10px; font-weight: bold; }
            .doclib-notice-wrapper { padding: 15px; border-radius: 6px; position: relative; margin: 10px 0; }
            .doclib-notice-wrapper--info { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
            .doclib-notice-wrapper--warning { background-color: #fff3e0; border-left: 4px solid #ff9800; }
            .doclib-notice-wrapper--spoiler { background-color: #f5f5f5; border-left: 4px solid #9e9e9e; filter: blur(4px); transition: filter 0.3s; cursor: pointer; }
            .doclib-notice-wrapper--spoiler:hover, .doclib-notice-wrapper--spoiler.revealed { filter: none; cursor: auto; }
        `;
      document.head.appendChild(style);

      document.addEventListener("click", (e: Event) => {
        const target = (e.target as HTMLElement).closest(
          ".doclib-notice-wrapper--spoiler",
        );
        if (target) {
          target.classList.add("revealed");
        }
      });
    }

    return tuneWrapper;
  }

  wrap(blockContent: HTMLElement) {
    this.wrapper = document.createElement("div");
    if (this.data.style) {
      this.wrapper.classList.add(
        "doclib-notice-wrapper",
        `doclib-notice-wrapper--${this.data.style}`,
      );
      this.wrapper.appendChild(this.input);
    }
    this.wrapper.appendChild(blockContent);
    return this.wrapper;
  }

  private applyStyle(style: string | undefined) {
    if (this.wrapper) {
      if (this.data.style) {
        this.wrapper.classList.remove(
          "doclib-notice-wrapper",
          `doclib-notice-wrapper--${this.data.style}`,
        );
        if (this.input.parentElement === this.wrapper)
          this.wrapper.removeChild(this.input);
      }

      this.data.style = style;

      if (this.data.style) {
        this.wrapper.classList.add(
          "doclib-notice-wrapper",
          `doclib-notice-wrapper--${this.data.style}`,
        );
        this.wrapper.prepend(this.input);
      }
    }
  }

  save() {
    if (!this.data.style) return undefined;
    return this.data;
  }
}
