import { API, BlockTune } from "@editorjs/editorjs";
import { IconAlignLeft, IconAlignCenter, IconAlignRight, IconAlignJustify } from '@codexteam/icons';

export default class DocLibAlignmentTune implements BlockTune {
  private api: API;
  private data: any;
  private block: any;
  private wrapper: HTMLElement | null = null;
  private alignments = [
    { name: "left", icon: IconAlignLeft, title: "DocLib Align Left" },
    { name: "center", icon: IconAlignCenter, title: "DocLib Align Center" },
    { name: "right", icon: IconAlignRight, title: "DocLib Align Right" },
    { name: "justify", icon: IconAlignJustify, title: "DocLib Justify" }
  ];

  static get isTune() { return true; }

  constructor({ api, data, block }: any) {
    this.api = api;
    this.data = data || { alignment: "left" };
    this.block = block;
  }

  render() {
    this.wrapper = document.createElement("div");

    this.alignments.forEach(align => {
      const btn = document.createElement("button");
      btn.classList.add(this.api.styles.settingsButton);
      btn.type = 'button';
      btn.innerHTML = align.icon;

      if (this.data.alignment === align.name) {
        btn.classList.add(this.api.styles.settingsButtonActive);
      }

      btn.addEventListener("click", () => {
        this.data.alignment = align.name;
        this.applyAlignment();
        
        
        Array.from(this.wrapper!.children).forEach((child: any) => {
          child.classList.remove(this.api.styles.settingsButtonActive);
        });
        btn.classList.add(this.api.styles.settingsButtonActive);
      });

      this.wrapper!.appendChild(btn);
    });

    return this.wrapper;
  }

  wrap(blockContent: HTMLElement) {
    if (this.data && this.data.alignment) {
      blockContent.style.textAlign = this.data.alignment;
      blockContent.style.width = "100%";
      blockContent.style.display = "block";
    }
    return blockContent;
  }

  applyAlignment() {
    const idx = this.api.blocks.getCurrentBlockIndex();
    if (idx !== undefined && idx >= 0) {
      const blockContent = this.api.blocks.getBlockByIndex(idx)?.holder;
      if (blockContent) {
         blockContent.style.textAlign = this.data.alignment;
         blockContent.style.width = "100%";
         blockContent.style.display = "block";
      }
    }
  }

  save() {
    return this.data;
  }
}
