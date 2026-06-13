import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibGist implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { url: string; file: string };

  static get toolbox() {
    return {
      title: "DocLib Gist",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  constructor({ api, data }: { api: API; data: any }) {
    this.api = api;
    this.data = {
      url: data.url || "",
      file: data.file || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-gist-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-gist-styles";
      style.innerHTML = `
        .doclib-gist-wrapper { margin: 16px 0; }
        .doclib-gist-iframe { width: 100%; min-height: 200px; border: none; }
        .doclib-gist-input-container { display: flex; align-items: center; gap: 8px; }
        .doclib-gist-input { flex-grow: 1; }
      `;
      document.head.appendChild(style);
    }

    this.wrapper.classList.add("doclib-gist-wrapper");
    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    if (this.data.url) {
      const iframe = document.createElement("iframe");
      iframe.classList.add("doclib-gist-iframe");

      const gistUrl =
        this.data.url + (this.data.file ? `?file=${this.data.file}` : "");
      const html = `
        <html>
          <head><base target="_parent"></head>
          <body style="margin:0;padding:0;">
            <script src="${gistUrl}.js"></script>
          </body>
        </html>
      `;

      iframe.srcdoc = html;

      iframe.onload = () => {
        try {
          if (iframe.contentWindow?.document?.body) {
            iframe.style.height =
              iframe.contentWindow.document.body.scrollHeight + 10 + "px";
          }
        } catch (e) {}
      };

      this.wrapper.appendChild(iframe);

      const editBtn = document.createElement("button");
      editBtn.classList.add("doclib-table-btn");
      editBtn.style.marginTop = "8px";
      editBtn.innerText = "Edit Gist Link";
      editBtn.addEventListener("click", () => {
        this.data.url = "";
        this.buildUI();
      });
      this.wrapper.appendChild(editBtn);
    } else {
      const container = document.createElement("div");
      container.classList.add("doclib-gist-input-container");

      const urlInput = document.createElement("input");
      urlInput.classList.add(this.api.styles.input, "doclib-gist-input");
      urlInput.placeholder =
        "URL GitHub Gist (VD: https://gist.github.com/user/id)";
      urlInput.value = this.data.url;

      const fileInput = document.createElement("input");
      fileInput.classList.add(this.api.styles.input);
      fileInput.style.width = "150px";
      fileInput.placeholder = "File name (optional)";
      fileInput.value = this.data.file;

      const btn = document.createElement("button");
      btn.classList.add(this.api.styles.button);
      btn.innerText = "Embed Gist";

      const insertGist = () => {
        if (urlInput.value && urlInput.value.includes("gist.github.com")) {
          this.data.url = urlInput.value.replace(/\.js$/, "");
          this.data.file = fileInput.value;
          this.buildUI();
        } else {
          urlInput.value = "";
          urlInput.placeholder = "Invalid Gist link!";
        }
      };

      btn.addEventListener("click", insertGist);

      container.appendChild(urlInput);
      container.appendChild(fileInput);
      container.appendChild(btn);
      this.wrapper.appendChild(container);
    }
  }

  save() {
    return this.data;
  }
}
