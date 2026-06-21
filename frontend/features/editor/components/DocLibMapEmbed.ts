import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibMapEmbed implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { lat: number; lng: number; zoom: number; label: string };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Map",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      lat: data?.lat ?? 21.0285,
      lng: data?.lng ?? 105.8542,
      zoom: data?.zoom ?? 13,
      label: data?.label || "",
    };
  }

  private buildMapUrl() {
    return `https://www.openstreetmap.org/export/embed.html?bbox=${this.data.lng - 0.05},${this.data.lat - 0.05},${this.data.lng + 0.05},${this.data.lat + 0.05}&layer=mapnik&marker=${this.data.lat},${this.data.lng}`;
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-map-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-map-styles";
      style.innerHTML = `
        .doclib-map-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin: 12px 0; }
        .doclib-map-controls { padding: 12px 16px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
        .doclib-map-input { flex: 1; min-width: 180px; padding: 8px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px; outline: none; }
        .doclib-map-btn { padding: 8px 14px; background: #0f172a; color: #fff; border: none; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; white-space: nowrap; }
        .doclib-map-btn:hover { background: #1e293b; }
        .doclib-map-iframe { width: 100%; height: 360px; border: none; display: block; }
        .doclib-map-label { font-size: 12px; color: #64748b; padding: 8px 16px; background: #f8fafc; border-top: 1px solid #e2e8f0; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-map-wrapper");

    const iframe = document.createElement("iframe");
    iframe.classList.add("doclib-map-iframe");
    iframe.setAttribute("allowfullscreen", "");
    iframe.src = this.buildMapUrl();

    const labelBar = document.createElement("div");
    labelBar.classList.add("doclib-map-label");
    labelBar.innerText = ` ${this.data.label}`;

    if (this.readOnly) {
      this.wrapper.appendChild(iframe);
      this.wrapper.appendChild(labelBar);
      return;
    }

    const controls = document.createElement("div");
    controls.classList.add("doclib-map-controls");

    const input = document.createElement("input");
    input.classList.add("doclib-map-input");
    input.placeholder = "DocLib Input";
    input.value = this.data.label;

    const searchBtn = document.createElement("button");
    searchBtn.classList.add("doclib-map-btn");
    searchBtn.innerText = "Search";

    const search = async () => {
      const q = input.value.trim();
      if (!q) return;
      searchBtn.innerText = "Searching";
      try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=1`);
        const results = await res.json();
        if (results && results.length > 0) {
          this.data.lat = parseFloat(results[0].lat);
          this.data.lng = parseFloat(results[0].lon);
          this.data.label = results[0].display_name;
          input.value = results[0].display_name;
          iframe.src = this.buildMapUrl();
          labelBar.innerText = ` ${this.data.label}`;
        } else {
          input.value = "No results found";
        }
      } catch (e) {
        input.value = "Search error";
      }
      searchBtn.innerText = "Search";
    };

    searchBtn.addEventListener("click", search);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") search(); });

    controls.appendChild(input);
    controls.appendChild(searchBtn);

    this.wrapper.appendChild(controls);
    this.wrapper.appendChild(iframe);
    this.wrapper.appendChild(labelBar);
  }

  save() {
    return this.data;
  }
}
