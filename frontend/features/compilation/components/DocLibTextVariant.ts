import { API } from "@editorjs/editorjs";

export default class DocLibTextVariant {
  static readonly feature = {
    id: "DocLibTextVariant",
    title: "Text Variant",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ca8d3865d094b68e"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="19,9 9,20 8,16 16,10 18,9 8,12"/></svg>',
    product: "doclib",
  } as const;

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
        icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ca8d3865d094b68e"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="19,9 9,20 8,16 16,10 18,9 8,12"/></svg>',
        title: "Text Variant",
      },
      {
        name: "citation",
        icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ca8d3865d094b68e"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="19,9 9,20 8,16 16,10 18,9 8,12"/></svg>',
        title: "Text Variant",
      },
      {
        name: "details",
        icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="ca8d3865d094b68e"><rect x="4" y="4" width="16" height="16" rx="3"/><polyline points="19,9 9,20 8,16 16,10 18,9 8,12"/></svg>',
        title: "Text Variant",
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
