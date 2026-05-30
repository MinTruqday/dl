import { API, BlockTool } from "@editorjs/editorjs";
import { IconDelimiter } from "@codexteam/icons";

export default class DocLibDelimiter implements BlockTool {
  private api: API;
  private data: any;
  private wrapper: HTMLElement | null = null;

  static get toolbox() {
    return {
      title: "DocLib Delimiter",
      icon: IconDelimiter
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = data || {};
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    // Create the three asterisks style mimicking original delimiter
    const asterisks = document.createElement('div');
    asterisks.classList.add('ce-delimiter');
    asterisks.style.lineHeight = '1.6em';
    asterisks.style.width = '100%';
    asterisks.style.textAlign = 'center';
    asterisks.style.color = '#7e838b';
    asterisks.style.fontSize = '30px';
    asterisks.style.letterSpacing = '0.2em';
    asterisks.innerHTML = '***';

    this.wrapper.appendChild(asterisks);
    return this.wrapper;
  }

  save() {
    return {}; // Delimiter has no data to save
  }
}
