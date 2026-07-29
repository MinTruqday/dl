import { API, BlockTool } from "@editorjs/editorjs";

interface MindNode {
  id: string;
  text: string;
  children: MindNode[];
}

export default class DocLibMindMap implements BlockTool {
  static readonly feature = {
    id: "DocLibMindMap",
    title: "DocLib Mind Map",
    icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b00415978b0509aa"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,8 8,19 7,9 13,4 15,5 12,7"/></svg>',
    product: "doclib",
  } as const;

  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { root: MindNode };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Mind Map",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" data-doclib-icon="b00415978b0509aa"><rect x="7" y="7" width="10" height="10" rx="3"/><polyline points="10,8 8,19 7,9 13,4 15,5 12,7"/></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  private mkId() {
    return Math.random().toString(36).slice(2, 8);
  }

  constructor({
    api,
    data,
    readOnly,
  }: {
    api: API;
    data: any;
    readOnly?: boolean;
  }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      root: data?.root || {
        id: this.mkId(),
        text: "Main idea",
        children: [
          {
            id: this.mkId(),
            text: "Branch 1",
            children: [
              { id: this.mkId(), text: "Idea 1.1", children: [] },
              { id: this.mkId(), text: "Idea 1.2", children: [] },
            ],
          },
          {
            id: this.mkId(),
            text: "Branch 2",
            children: [{ id: this.mkId(), text: "Idea 2.1", children: [] }],
          },
          { id: this.mkId(), text: "Branch 3", children: [] },
        ],
      },
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-mm-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-mm-styles";
      style.innerHTML = `
        .doclib-mm-wrapper { border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; background: #fff; margin: 12px 0; overflow-x: auto; }
        .doclib-mm-tree { display: flex; align-items: flex-start; gap: 0; }
        .doclib-mm-node-wrap { display: flex; align-items: center; }
        .doclib-mm-children { display: flex; flex-direction: column; justify-content: center; gap: 0; position: relative; }
        .doclib-mm-child-row { display: flex; align-items: center; }
        .doclib-mm-connector-h { width: 32px; height: 2px; background: #e2e8f0; flex-shrink: 0; }
        .doclib-mm-connector-v { width: 2px; background: #e2e8f0; position: absolute; left: 0; }
        .doclib-mm-node { padding: 8px 14px; border: 2px solid #e2e8f0; border-radius: 20px; font-size: 13px; font-weight: 500; color: #1e293b; background: #fff; white-space: nowrap; cursor: pointer; user-select: none; }
        .doclib-mm-node.root { border-color: #0284c7; background: #f0f9ff; color: #0c4a6e; font-weight: 700; font-size: 15px; }
        .doclib-mm-node:hover { border-color: #0284c7; }
        .doclib-mm-node-actions { display: flex; gap: 3px; margin-left: 6px; }
        .doclib-mm-node-btn { padding: 2px 6px; border: 1px solid #e2e8f0; border-radius: 4px; background: #fff; font-size: 11px; cursor: pointer; color: #64748b; }
        .doclib-mm-node-btn:hover { background: #f0f9ff; color: #0284c7; border-color: #0284c7; }
        .doclib-mm-inline-input { font-size: 13px; font-weight: 500; border: none; outline: 2px solid #0284c7; border-radius: 20px; padding: 6px 12px; background: #f0f9ff; color: #0c4a6e; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private renderNode(node: MindNode, isRoot = false): HTMLElement {
    const wrap = document.createElement("div");
    wrap.classList.add("doclib-mm-node-wrap");

    const nodeEl = document.createElement("div");
    nodeEl.classList.add("doclib-mm-node");
    if (isRoot) nodeEl.classList.add("root");
    nodeEl.innerText = node.text;

    if (!this.readOnly) {
      nodeEl.addEventListener("dblclick", (e) => {
        e.stopPropagation();
        const input = document.createElement("input");
        input.classList.add("doclib-mm-inline-input");
        input.value = node.text;
        nodeEl.replaceWith(input);
        input.focus();
        const finish = () => {
          node.text = input.value || node.text;
          input.replaceWith(nodeEl);
          nodeEl.innerText = node.text;
        };
        input.addEventListener("blur", finish);
        input.addEventListener("keydown", (e) => {
          if (e.key === "Enter") finish();
        });
      });

      const actions = document.createElement("div");
      actions.classList.add("doclib-mm-node-actions");

      const addBtn = document.createElement("button");
      addBtn.classList.add("doclib-mm-node-btn");
      addBtn.innerText = "+";
      addBtn.title = "Add child branch";
      addBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        node.children.push({
          id: this.mkId(),
          text: "New branch",
          children: [],
        });
        this.buildUI();
      });
      actions.appendChild(addBtn);

      if (!isRoot) {
        const delBtn = document.createElement("button");
        delBtn.classList.add("doclib-mm-node-btn");
        delBtn.innerText = "x";
        delBtn.title = "Remove branch";
        delBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.deleteNode(this.data.root, node.id);
          this.buildUI();
        });
        actions.appendChild(delBtn);
      }

      wrap.appendChild(nodeEl);
      wrap.appendChild(actions);
    } else {
      wrap.appendChild(nodeEl);
    }

    if (node.children.length > 0) {
      const connector = document.createElement("div");
      connector.classList.add("doclib-mm-connector-h");
      wrap.appendChild(connector);

      const childrenWrap = document.createElement("div");
      childrenWrap.classList.add("doclib-mm-children");

      const childElements = node.children.map((child) => {
        const childRow = document.createElement("div");
        childRow.classList.add("doclib-mm-child-row");
        const childNode = this.renderNode(child);
        childRow.appendChild(childNode);
        return childRow;
      });

      childElements.forEach((el) => childrenWrap.appendChild(el));

      if (node.children.length > 1) {
        const firstRow = childElements[0];
        const lastRow = childElements[node.children.length - 1];
        requestAnimationFrame(() => {
          const parentTop = childrenWrap.getBoundingClientRect().top;
          const firstTop =
            firstRow.getBoundingClientRect().top + firstRow.offsetHeight / 2;
          const lastTop =
            lastRow.getBoundingClientRect().top + lastRow.offsetHeight / 2;
          const line = document.createElement("div");
          line.classList.add("doclib-mm-connector-v");
          line.style.top = `${firstTop - parentTop}px`;
          line.style.height = `${lastTop - firstTop}px`;
          childrenWrap.appendChild(line);
        });
      }

      wrap.appendChild(childrenWrap);
    }

    return wrap;
  }

  private deleteNode(parent: MindNode, targetId: string): boolean {
    const idx = parent.children.findIndex((c) => c.id === targetId);
    if (idx !== -1) {
      parent.children.splice(idx, 1);
      return true;
    }
    return parent.children.some((c) => this.deleteNode(c, targetId));
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-mm-wrapper");

    if (!this.readOnly) {
      const hint = document.createElement("div");
      hint.style.cssText = "font-size:11px;color:#94a3b8;margin-bottom:12px;";
      hint.innerText = "Double-click to edit    + to add branch    x to remove";
      this.wrapper.appendChild(hint);
    }

    const tree = document.createElement("div");
    tree.classList.add("doclib-mm-tree");
    tree.appendChild(this.renderNode(this.data.root, true));
    this.wrapper.appendChild(tree);
  }

  save() {
    return this.data;
  }
}
