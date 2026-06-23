import { API, BlockTool, BlockToolData } from "@editorjs/editorjs";

export default class DocLibTournamentBracket implements BlockTool {
  private api: API;
  private readOnly: boolean;
  private data: any;
  private wrapper!: HTMLElement;

  static get toolbox() {
    return {
      title: "DocLib Tournament Bracket",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"></polyline><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      t1: data?.t1 || "", t2: data?.t2 || "",
      t3: data?.t3 || "", t4: data?.t4 || "",
      s1: data?.s1 || "", s2: data?.s2 || "",
      w: data?.w || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);
    
    const style = document.createElement("style");
    style.innerHTML = `
      .doclib-bracket { display: flex; font-family: sans-serif; background: #f8fafc; padding: 24px; border-radius: 8px; overflow-x: auto; min-width: 600px; justify-content: center; }
      .doclib-b-col { display: flex; flex-direction: column; justify-content: space-around; width: 180px; position: relative; }
      .doclib-b-match { position: relative; display: flex; flex-direction: column; gap: 2px; }
      .doclib-b-team { background: #fff; border: 1px solid #cbd5e1; padding: 8px; border-radius: 4px; font-size: 14px; font-weight: bold; color: #1e293b; outline: none; }
      .doclib-b-team:empty:before { content: attr(data-placeholder); color: #94a3b8; font-weight: normal; }
      .doclib-b-connector-r { position: absolute; right: -20px; top: 50%; width: 20px; border-top: 2px solid #94a3b8; }
      .doclib-b-connector-v { position: absolute; right: -20px; top: 25%; bottom: 25%; border-right: 2px solid #94a3b8; }
      .doclib-b-connector-l { position: absolute; left: -20px; top: 50%; width: 20px; border-top: 2px solid #94a3b8; }
    `;
    this.wrapper.appendChild(style);

    const container = document.createElement("div");
    container.classList.add("doclib-bracket");

    const createTeam = (key: string) => {
      const el = document.createElement("div");
      el.classList.add("doclib-b-team");
      el.innerText = this.data[key];
      el.dataset.placeholder = "DocLib Team";
      if (!this.readOnly) {
        el.contentEditable = "true";
        el.addEventListener("input", () => { this.data[key] = el.innerText; });
      }
      return el;
    };

    const col1 = document.createElement("div");
    col1.classList.add("doclib-b-col");
    
    const m1 = document.createElement("div");
    m1.classList.add("doclib-b-match");
    m1.style.marginBottom = "40px";
    m1.appendChild(createTeam("t1"));
    m1.appendChild(createTeam("t2"));
    const c1 = document.createElement("div");
    c1.classList.add("doclib-b-connector-r");
    m1.appendChild(c1);

    const m2 = document.createElement("div");
    m2.classList.add("doclib-b-match");
    m2.appendChild(createTeam("t3"));
    m2.appendChild(createTeam("t4"));
    const c2 = document.createElement("div");
    c2.classList.add("doclib-b-connector-r");
    m2.appendChild(c2);

    const cv = document.createElement("div");
    cv.classList.add("doclib-b-connector-v");
    cv.style.top = "20%"; cv.style.bottom = "20%";
    col1.appendChild(cv);
    col1.appendChild(m1);
    col1.appendChild(m2);

    const col2 = document.createElement("div");
    col2.classList.add("doclib-b-col");
    col2.style.marginLeft = "40px";
    
    const m3 = document.createElement("div");
    m3.classList.add("doclib-b-match");
    m3.appendChild(createTeam("s1"));
    m3.appendChild(createTeam("s2"));
    const c3 = document.createElement("div");
    c3.classList.add("doclib-b-connector-l");
    const c4 = document.createElement("div");
    c4.classList.add("doclib-b-connector-r");
    m3.appendChild(c3);
    m3.appendChild(c4);

    col2.appendChild(m3);

    const col3 = document.createElement("div");
    col3.classList.add("doclib-b-col");
    col3.style.marginLeft = "40px";
    
    const m4 = document.createElement("div");
    m4.classList.add("doclib-b-match");
    const winner = createTeam("w");
    winner.style.borderColor = "#f59e0b";
    winner.style.background = "#fffbeb";
    m4.appendChild(winner);
    const c5 = document.createElement("div");
    c5.classList.add("doclib-b-connector-l");
    m4.appendChild(c5);

    col3.appendChild(m4);

    container.appendChild(col1);
    container.appendChild(col2);
    container.appendChild(col3);

    this.wrapper.appendChild(container);
    return this.wrapper;
  }

  save(blockContent: HTMLElement): BlockToolData {
    return this.data;
  }
}
