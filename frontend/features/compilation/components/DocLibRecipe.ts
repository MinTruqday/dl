// @ts-nocheck
import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibRecipe implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    title: string;
    description: string;
    prepTime: string;
    cookTime: string;
    servings: string;
    difficulty: string;
    ingredients: string[];
    steps: string[];
    image: string;
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Recipe",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 11h.01"></path><path d="M11 15h.01"></path><path d="M16 16h.01"></path><path d="m2 16 20 6-6-20A20 20 0 0 0 2 16"></path><path d="M5.71 17.11a17.04 17.04 0 0 1 11.4-11.4"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
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
      title: data?.title || "",
      description: data?.description || "",
      prepTime: data?.prepTime || "",
      cookTime: data?.cookTime || "",
      servings: data?.servings || "",
      difficulty: data?.difficulty || "",
      ingredients: data?.ingredients || [],
      steps: data?.steps || [],
      image: data?.image || "",
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-recipe-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-recipe-styles";
      style.innerHTML = `
        .doclib-recipe-wrapper { border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; margin: 12px 0; background: #fff; }
        .doclib-recipe-header { padding: 24px; border-bottom: 1px solid #f1f5f9; }
        .doclib-recipe-title { font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 6px; }
        .doclib-recipe-desc { font-size: 14px; color: #64748b; line-height: 1.5; }
        .doclib-recipe-meta { display: flex; flex-wrap: wrap; gap: 16px; padding: 16px 24px; background: #f8fafc; border-bottom: 1px solid #f1f5f9; }
        .doclib-recipe-meta-item { display: flex; flex-direction: column; align-items: center; gap: 2px; }
        .doclib-recipe-meta-icon { font-size: 18px; }
        .doclib-recipe-meta-label { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; }
        .doclib-recipe-meta-value { font-size: 13px; font-weight: 600; color: #0f172a; }
        .doclib-recipe-body { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
        .doclib-recipe-section { padding: 20px 24px; }
        .doclib-recipe-section:first-child { border-right: 1px solid #f1f5f9; }
        .doclib-recipe-section-title { font-size: 13px; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }
        .doclib-recipe-ingredient { padding: 6px 0; font-size: 14px; color: #475569; border-bottom: 1px solid #f8fafc; display: flex; align-items: center; gap: 8px; }
        .doclib-recipe-ingredient::before { content: ""; color: #0284c7; font-weight: bold; }
        .doclib-recipe-step { display: flex; gap: 12px; margin-bottom: 12px; }
        .doclib-recipe-step-num { width: 24px; height: 24px; border-radius: 50%; background: #0284c7; color: #fff; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px; }
        .doclib-recipe-step-text { font-size: 14px; color: #475569; line-height: 1.5; }
        .doclib-recipe-edit { background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 24px; }
        .doclib-recipe-edit-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
        .doclib-recipe-field { display: flex; flex-direction: column; gap: 3px; }
        .doclib-recipe-field label { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; }
        .doclib-recipe-field input, .doclib-recipe-field textarea { padding: 7px 9px; border: 1px solid #e2e8f0; border-radius: 5px; font-size: 12px; outline: none; font-family: inherit; }
        .doclib-recipe-list-edit { display: flex; flex-direction: column; gap: 4px; }
        .doclib-recipe-list-row { display: flex; gap: 6px; align-items: center; }
        .doclib-recipe-list-input { flex: 1; padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 12px; outline: none; }
        .doclib-recipe-list-del { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; }
        .doclib-recipe-add-btn { padding: 6px 12px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 11px; cursor: pointer; margin-top: 4px; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";
    this.wrapper.classList.add("doclib-recipe-wrapper");

    const header = document.createElement("div");
    header.classList.add("doclib-recipe-header");

    const title = document.createElement("div");
    title.classList.add("doclib-recipe-title");
    title.innerText = this.data.title;

    const desc = document.createElement("div");
    desc.classList.add("doclib-recipe-desc");
    desc.innerText = this.data.description;

    header.appendChild(title);
    header.appendChild(desc);

    const meta = document.createElement("div");
    meta.classList.add("doclib-recipe-meta");

    const metaItems = [
      { icon: "", label: "Prep", value: this.data.prepTime },
      { icon: "", label: "Cook", value: this.data.cookTime },
      { icon: "️", label: "Servings", value: `${this.data.servings} servings` },
      { icon: "", label: "Difficulty", value: this.data.difficulty },
    ];

    metaItems.forEach(({ icon, label, value }) => {
      const item = document.createElement("div");
      item.classList.add("doclib-recipe-meta-item");
      item.innerHTML = `<span class="doclib-recipe-meta-icon">${icon}</span><span class="doclib-recipe-meta-label">${label}</span><span class="doclib-recipe-meta-value">${value}</span>`;
      meta.appendChild(item);
    });

    const body = document.createElement("div");
    body.classList.add("doclib-recipe-body");

    const ingredientsSection = document.createElement("div");
    ingredientsSection.classList.add("doclib-recipe-section");
    const ingTitle = document.createElement("div");
    ingTitle.classList.add("doclib-recipe-section-title");
    ingTitle.innerText = "Ingredients";
    ingredientsSection.appendChild(ingTitle);
    this.data.ingredients.forEach((ing) => {
      const item = document.createElement("div");
      item.classList.add("doclib-recipe-ingredient");
      item.innerText = ing;
      ingredientsSection.appendChild(item);
    });

    const stepsSection = document.createElement("div");
    stepsSection.classList.add("doclib-recipe-section");
    const stepsTitle = document.createElement("div");
    stepsTitle.classList.add("doclib-recipe-section-title");
    stepsTitle.innerText = "Instructions";
    stepsSection.appendChild(stepsTitle);
    this.data.steps.forEach((step, i) => {
      const row = document.createElement("div");
      row.classList.add("doclib-recipe-step");
      const num = document.createElement("div");
      num.classList.add("doclib-recipe-step-num");
      num.innerText = `${i + 1}`;
      const text = document.createElement("div");
      text.classList.add("doclib-recipe-step-text");
      text.innerText = step;
      row.appendChild(num);
      row.appendChild(text);
      stepsSection.appendChild(row);
    });

    body.appendChild(ingredientsSection);
    body.appendChild(stepsSection);

    this.wrapper.appendChild(header);
    this.wrapper.appendChild(meta);
    this.wrapper.appendChild(body);

    if (!this.readOnly) {
      const edit = document.createElement("div");
      edit.classList.add("doclib-recipe-edit");

      const infoGrid = document.createElement("div");
      infoGrid.classList.add("doclib-recipe-edit-grid");

      const infoFields: { key: keyof typeof this.data; label: string }[] = [
        { key: "title", label: "Recipe name" },
        { key: "difficulty", label: "Difficulty" },
        { key: "prepTime", label: "Prep" },
        { key: "cookTime", label: "Cook" },
        { key: "servings", label: "Servings" },
      ];

      infoFields.forEach(({ key, label }) => {
        const field = document.createElement("div");
        field.classList.add("doclib-recipe-field");
        const lbl = document.createElement("label");
        lbl.innerText = label;
        const input = document.createElement("input");
        input.value = this.data[key] as string;
        input.addEventListener("input", () => {
          (this.data as any)[key] = input.value;
          this.buildUI();
        });
        field.appendChild(lbl);
        field.appendChild(input);
        infoGrid.appendChild(field);
      });

      edit.appendChild(infoGrid);

      const buildListEditor = (
        label: string,
        items: string[],
        onUpdate: (items: string[]) => void,
      ) => {
        const section = document.createElement("div");
        const lbl = document.createElement("div");
        lbl.style.cssText =
          "font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;margin-bottom:6px;";
        lbl.innerText = label;
        section.appendChild(lbl);

        const listEdit = document.createElement("div");
        listEdit.classList.add("doclib-recipe-list-edit");

        const renderRows = () => {
          listEdit.innerHTML = "";
          items.forEach((item, i) => {
            const row = document.createElement("div");
            row.classList.add("doclib-recipe-list-row");
            const input = document.createElement("input");
            input.classList.add("doclib-recipe-list-input");
            input.value = item;
            input.addEventListener("input", () => {
              items[i] = input.value;
              onUpdate(items);
            });
            const del = document.createElement("button");
            del.classList.add("doclib-recipe-list-del");
            del.innerText = "x";
            del.addEventListener("click", () => {
              items.splice(i, 1);
              renderRows();
              onUpdate(items);
            });
            row.appendChild(input);
            row.appendChild(del);
            listEdit.appendChild(row);
          });
          const addBtn = document.createElement("button");
          addBtn.classList.add("doclib-recipe-add-btn");
          addBtn.innerText = "Add";
          addBtn.addEventListener("click", () => {
            items.push("");
            renderRows();
            onUpdate(items);
          });
          listEdit.appendChild(addBtn);
        };

        renderRows();
        section.appendChild(listEdit);
        return section;
      };

      edit.appendChild(
        buildListEditor("Ingredients", this.data.ingredients, () => {}),
      );
      edit.appendChild(buildListEditor("Steps", this.data.steps, () => {}));

      this.wrapper.appendChild(edit);
    }
  }

  save() {
    return this.data;
  }
}
