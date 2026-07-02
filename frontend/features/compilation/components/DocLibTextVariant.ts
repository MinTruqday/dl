import { API } from "@editorjs/editorjs";

export default class DocLibTextVariant {
  private api: API;
  private data: string;
  private wrapper: HTMLElement | null = null;
  private block: any;
  private variants: any[];

  static get isTune() {
    return true;
  }

  constructor({ api, data, block }: { api: API; data: any; block: any }) {
    this.api = api;
    this.data = data || "";
    this.block = block;

    this.variants = [
      {
        name: "call-out",
        icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 21h4v-2h-4v2zm2-17c-3.31 0-6 2.69-6 6 0 2.22 1.21 4.15 3 5.19V17c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1.81c1.79-1.04 3-2.97 3-5.19 0-3.31-2.69-6-6-6zm-1 12h2v-2h-2v2zm1-9c1.1 0 2 .9 2 2 0 1.11-.89 2-2 2s-2-.89-2-2c0-1.1.9-2 2-2z"/></svg>',
        title: "Call-out",
      },
      {
        name: "citation",
        icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 4h-3L9 11v9h9v-9h-3.5zm-11 0h-3L1 11v9h9v-9H6.5z"/></svg>',
        title: "Citation",
      },
      {
        name: "details",
        icon: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 17h2v-6h-2v6zm1-15C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zM11 9h2V7h-2v2z"/></svg>',
        title: "Details",
      },
    ];
  }

  render() {
    const tuneWrapper = document.createElement("div");

    this.variants.forEach(({ name, icon, title }) => {
      const toggler = document.createElement("div");
      toggler.classList.add(this.api.styles.settingsButton);
      toggler.innerHTML = icon;

      if (this.data === name) {
        toggler.classList.add(this.api.styles.settingsButtonActive);
      }

      this.api.tooltip.onHover(toggler, title, {
        placement: "top",
        hidingDelay: 500,
      });

      toggler.addEventListener("click", () => {
        const isEnabled = toggler.classList.contains(
          this.api.styles.settingsButtonActive,
        );

        Array.from(tuneWrapper.children).forEach((btn) =>
          btn.classList.remove(this.api.styles.settingsButtonActive),
        );

        if (!isEnabled) {
          toggler.classList.add(this.api.styles.settingsButtonActive);
          this.variant = name;
        } else {
          this.variant = "";
        }

        this.block.dispatchChange();
      });

      tuneWrapper.appendChild(toggler);
    });

    return tuneWrapper;
  }

  wrap(blockContent: HTMLElement) {
    this.wrapper = document.createElement("div");
    this.variant = this.data;
    this.wrapper.appendChild(blockContent);

    if (!document.getElementById("doclib-text-variant-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-text-variant-styles";
      style.innerHTML = `
            .cdx-text-variant--call-out { border: 1px solid #e1e1e1; padding: 15px; border-radius: 5px; background: #fafafa; }
            .cdx-text-variant--citation { font-style: italic; border-left: 3px solid #000; padding-left: 10px; color: #555; }
            .cdx-text-variant--details { font-size: 0.85em; color: #666; }
        `;
      document.head.appendChild(style);
    }

    return this.wrapper;
  }

  set variant(name: string) {
    this.data = name;
    if (this.wrapper) {
      this.variants.forEach((v) => {
        this.wrapper!.classList.toggle(
          `cdx-text-variant--${v.name}`,
          v.name === this.data,
        );
      });
    }
  }

  save() {
    return this.data || "";
  }
}
