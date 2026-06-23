import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibSmartArtRelationship implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib SmartArt Relationship",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><circle cx="6" cy="6" r="2"></circle><circle cx="18" cy="18" r="2"></circle><circle cx="18" cy="6" r="2"></circle><circle cx="6" cy="18" r="2"></circle><line x1="7.5" y1="7.5" x2="10.5" y2="10.5"></line><line x1="16.5" y1="16.5" x2="13.5" y2="13.5"></line><line x1="16.5" y1="7.5" x2="13.5" y2="10.5"></line><line x1="7.5" y1="16.5" x2="10.5" y2="13.5"></line></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      center: data?.center || "DocLib Core",
      satellites: data?.satellites && data.satellites.length > 0 ? data.satellites : ["DocLib A", "DocLib B", "DocLib C", "DocLib D"],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-rel { width: 100%; max-width: 400px; aspect-ratio: 1/1; position: relative; margin: 24px auto; font-family: sans-serif; display: flex; align-items: center; justify-content: center; }
      .doclib-rel-center { width: 100px; height: 100px; background: #3b82f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: bold; text-align: center; font-size: 14px; position: relative; z-index: 10; outline: none; }
      .doclib-rel-center:empty:before { content: "DocLib Center"; color: #bfdbfe; }
      .doclib-rel-sat { width: 70px; height: 70px; background: #f8fafc; border: 2px solid #3b82f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #1e293b; font-weight: 600; text-align: center; font-size: 12px; position: absolute; outline: none; z-index: 20; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
      .doclib-rel-sat:empty:before { content: "DocLib Sat"; color: #94a3b8; }
      .doclib-rel-line { position: absolute; background: #cbd5e1; height: 2px; transform-origin: 0 50%; z-index: 5; }
      .doclib-rel-del { position: absolute; top: -5px; right: -5px; width: 18px; height: 18px; background: #ef4444; color: #fff; border-radius: 50%; font-size: 10px; display: none; align-items: center; justify-content: center; cursor: pointer; border: none; z-index: 30; }
      .doclib-rel-sat:hover .doclib-rel-del { display: flex; }
      .doclib-rel-add { position: absolute; bottom: -40px; left: 50%; transform: translateX(-50%); padding: 8px 16px; background: #f1f5f9; border: 1px dashed #cbd5e1; border-radius: 4px; font-size: 12px; color: #3b82f6; cursor: pointer; display: none; }
      .doclib-rel:hover .doclib-rel-add { display: block; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-rel");

    const center = document.createElement("div");
    center.classList.add("doclib-rel-center");
    center.innerText = this.data.center;
    if (!this.readOnly) {
      center.contentEditable = "true";
      center.addEventListener("input", () => { this.data.center = center.innerText; });
    }
    container.appendChild(center);

    const renderSatellites = () => {
      // Clear old satellites and lines
      Array.from(container.children).forEach(child => {
        if (child !== center && !child.classList.contains("doclib-rel-add")) {
          child.remove();
        }
      });

      const radius = 130;
      const count = this.data.satellites.length;
      const angleStep = (2 * Math.PI) / count;

      this.data.satellites.forEach((sat: string, i: number) => {
        const angle = i * angleStep - Math.PI / 2; // Start from top
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;

        // Line
        const line = document.createElement("div");
        line.classList.add("doclib-rel-line");
        line.style.width = `${radius}px`;
        line.style.left = "50%";
        line.style.top = "50%";
        line.style.transform = `translateY(-50%) rotate(${angle}rad)`;
        container.appendChild(line);

        // Satellite
        const satEl = document.createElement("div");
        satEl.classList.add("doclib-rel-sat");
        satEl.style.transform = `translate(${x}px, ${y}px)`;
        satEl.innerText = sat;

        if (!this.readOnly) {
          satEl.contentEditable = "true";
          satEl.addEventListener("input", () => { this.data.satellites[i] = satEl.innerText; });
          
          const del = document.createElement("button");
          del.classList.add("doclib-rel-del");
          del.innerText = "✕";
          del.contentEditable = "false";
          del.addEventListener("click", () => {
            this.data.satellites.splice(i, 1);
            renderSatellites();
          });
          satEl.appendChild(del);
        }
        
        container.appendChild(satEl);
      });
    };

    renderSatellites();

    if (!this.readOnly) {
      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-rel-add");
      addBtn.innerText = "+ Add Item";
      addBtn.addEventListener("click", () => {
        this.data.satellites.push("DocLib New");
        renderSatellites();
      });
      container.appendChild(addBtn);
    }

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
