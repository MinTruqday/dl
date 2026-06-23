import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibPricingTable implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: {
    tiers: { id: string; name: string; price: string; period: string; features: { text: string; included: boolean }[]; recommended: boolean; btnText: string; btnUrl: string; color: string }[];
  };
  private readOnly: boolean;

  static get toolbox() {
    return {
      title: "DocLib Pricing Table",
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
    };
  }

  static get isReadOnlySupported() {
    return true;
  }

  private mkId() { return Math.random().toString(36).substring(2, 8); }

  constructor({ api, data, readOnly }: { api: API; data: any; readOnly?: boolean }) {
    this.api = api;
    this.readOnly = !!readOnly;
    this.data = {
      tiers: data?.tiers || [],
    };
  }

  render() {
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add(this.api.styles.block);

    if (!document.getElementById("doclib-pricing-styles")) {
      const style = document.createElement("style");
      style.id = "doclib-pricing-styles";
      style.innerHTML = `
        .doclib-pr-wrapper { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; margin: 24px 0; }
        .doclib-pr-tier { flex: 1; min-width: 260px; max-width: 320px; background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px 24px; position: relative; display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; }
        .doclib-pr-tier:hover { transform: translateY(-4px); box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); }
        .doclib-pr-tier.recommended { border: 2px solid; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); }
        .doclib-pr-badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; }
        .doclib-pr-name { font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px; text-align: center; }
        .doclib-pr-price-box { text-align: center; margin-bottom: 24px; }
        .doclib-pr-price { font-size: 40px; font-weight: 800; line-height: 1; color: #0f172a; }
        .doclib-pr-period { font-size: 14px; color: #64748b; font-weight: 500; }
        .doclib-pr-features { flex: 1; display: flex; flex-direction: column; gap: 12px; margin-bottom: 32px; }
        .doclib-pr-feat { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #334155; }
        .doclib-pr-feat.excluded { color: #94a3b8; text-decoration: line-through; }
        .doclib-pr-icon-yes { color: #10b981; font-weight: bold; }
        .doclib-pr-icon-no { color: #cbd5e1; }
        .doclib-pr-btn { display: block; width: 100%; text-align: center; padding: 12px; border-radius: 8px; font-size: 15px; font-weight: 600; text-decoration: none; color: #fff; transition: opacity 0.2s; }
        .doclib-pr-btn:hover { opacity: 0.9; }
        .doclib-pr-edit { width: 100%; margin-top: 24px; padding: 20px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; }
        .doclib-pr-edit-tier { border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px; margin-bottom: 16px; background: #fff; }
        .doclib-pr-edit-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 16px; }
        .doclib-pr-input { width: 100%; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 13px; outline: none; box-sizing: border-box; }
        .doclib-pr-feat-edit { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
        .doclib-pr-del { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 16px; padding: 4px; }
        .doclib-pr-add-btn { padding: 8px 16px; background: #0f172a; color: #fff; border: none; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; }
        .doclib-pr-add-feat-btn { padding: 4px 10px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 11px; cursor: pointer; margin-top: 4px; }
      `;
      document.head.appendChild(style);
    }

    this.buildUI();
    return this.wrapper;
  }

  private buildUI() {
    if (!this.wrapper) return;
    this.wrapper.innerHTML = "";

    const displayWrap = document.createElement("div");
    displayWrap.classList.add("doclib-pr-wrapper");

    this.data.tiers.forEach((tier) => {
      const el = document.createElement("div");
      el.classList.add("doclib-pr-tier");
      if (tier.recommended) {
        el.classList.add("recommended");
        el.style.borderColor = tier.color;
        const badge = document.createElement("div");
        badge.classList.add("doclib-pr-badge");
        badge.style.background = tier.color;
        badge.innerText = "Most Popular";
        el.appendChild(badge);
      }

      const name = document.createElement("div");
      name.classList.add("doclib-pr-name");
      name.innerText = tier.name;

      const priceBox = document.createElement("div");
      priceBox.classList.add("doclib-pr-price-box");
      const price = document.createElement("span");
      price.classList.add("doclib-pr-price");
      price.innerText = tier.price;
      const period = document.createElement("span");
      period.classList.add("doclib-pr-period");
      period.innerText = tier.period;
      priceBox.appendChild(price);
      priceBox.appendChild(period);

      const features = document.createElement("div");
      features.classList.add("doclib-pr-features");
      tier.features.forEach((feat) => {
        const fEl = document.createElement("div");
        fEl.classList.add("doclib-pr-feat");
        if (!feat.included) fEl.classList.add("excluded");
        fEl.innerHTML = `<span class="${feat.included ? 'doclib-pr-icon-yes' : 'doclib-pr-icon-no'}">${feat.included ? 'v' : 'x'}</span><span>${feat.text}</span>`;
        features.appendChild(fEl);
      });

      const btn = document.createElement("a");
      btn.classList.add("doclib-pr-btn");
      btn.style.background = tier.color;
      btn.href = tier.btnUrl;
      btn.target = "_blank";
      btn.innerText = tier.btnText;

      el.appendChild(name);
      el.appendChild(priceBox);
      el.appendChild(features);
      el.appendChild(btn);
      displayWrap.appendChild(el);
    });

    this.wrapper.appendChild(displayWrap);

    if (!this.readOnly) {
      const editArea = document.createElement("div");
      editArea.classList.add("doclib-pr-edit");

      this.data.tiers.forEach((tier, tIdx) => {
        const tierEdit = document.createElement("div");
        tierEdit.classList.add("doclib-pr-edit-tier");

        const headerRow = document.createElement("div");
        headerRow.style.display = "flex";
        headerRow.style.justifyContent = "space-between";
        headerRow.style.alignItems = "center";
        headerRow.style.marginBottom = "16px";

        const title = document.createElement("strong");
        title.innerText = `Tier ${tIdx + 1}`;
        
        const removeTier = document.createElement("button");
        removeTier.classList.add("doclib-pr-del");
        removeTier.innerText = "Delete Tier";
        removeTier.addEventListener("click", () => { this.data.tiers.splice(tIdx, 1); this.buildUI(); });

        headerRow.appendChild(title);
        headerRow.appendChild(removeTier);
        tierEdit.appendChild(headerRow);

        const grid = document.createElement("div");
        grid.classList.add("doclib-pr-edit-grid");

        const mkInp = (label: string, val: string, update: (v: string) => void) => {
          const wrap = document.createElement("div");
          const l = document.createElement("label");
          l.style.cssText = "font-size:11px;color:#64748b;margin-bottom:4px;display:block;";
          l.innerText = label;
          const i = document.createElement("input");
          i.classList.add("doclib-pr-input");
          i.value = val;
          i.addEventListener("input", () => { update(i.value); this.buildUI(); });
          wrap.appendChild(l);
          wrap.appendChild(i);
          return wrap;
        };

        grid.appendChild(mkInp("Name", tier.name, (v) => tier.name = v));
        grid.appendChild(mkInp("Price", tier.price, (v) => tier.price = v));
        grid.appendChild(mkInp("Period", tier.period, (v) => tier.period = v));
        grid.appendChild(mkInp("Button Text", tier.btnText, (v) => tier.btnText = v));

        const colorWrap = document.createElement("div");
        const cLabel = document.createElement("label");
        cLabel.style.cssText = "font-size:11px;color:#64748b;margin-bottom:4px;display:block;";
        cLabel.innerText = "Color";
        const cInp = document.createElement("input");
        cInp.type = "color";
        cInp.value = tier.color;
        cInp.style.width = "100%";
        cInp.style.height = "34px";
        cInp.style.padding = "0";
        cInp.addEventListener("input", () => { tier.color = cInp.value; this.buildUI(); });
        colorWrap.appendChild(cLabel);
        colorWrap.appendChild(cInp);
        grid.appendChild(colorWrap);

        const recWrap = document.createElement("div");
        recWrap.style.display = "flex";
        recWrap.style.alignItems = "center";
        recWrap.style.gap = "8px";
        const recCb = document.createElement("input");
        recCb.type = "checkbox";
        recCb.checked = tier.recommended;
        recCb.addEventListener("change", () => { tier.recommended = recCb.checked; this.buildUI(); });
        const recLabel = document.createElement("span");
        recLabel.style.fontSize = "13px";
        recLabel.innerText = "Recommended";
        recWrap.appendChild(recCb);
        recWrap.appendChild(recLabel);
        grid.appendChild(recWrap);

        tierEdit.appendChild(grid);

        const featList = document.createElement("div");
        featList.style.marginTop = "16px";
        
        tier.features.forEach((feat, fIdx) => {
          const fRow = document.createElement("div");
          fRow.classList.add("doclib-pr-feat-edit");

          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.checked = feat.included;
          cb.addEventListener("change", () => { feat.included = cb.checked; this.buildUI(); });

          const inpt = document.createElement("input");
          inpt.classList.add("doclib-pr-input");
          inpt.value = feat.text;
          inpt.addEventListener("input", () => { feat.text = inpt.value; this.buildUI(); });

          const delF = document.createElement("button");
          delF.classList.add("doclib-pr-del");
          delF.innerText = "x";
          delF.addEventListener("click", () => { tier.features.splice(fIdx, 1); this.buildUI(); });

          fRow.appendChild(cb);
          fRow.appendChild(inpt);
          fRow.appendChild(delF);
          featList.appendChild(fRow);
        });

        const addFeatBtn = document.createElement("button");
        addFeatBtn.classList.add("doclib-pr-add-feat-btn");
        addFeatBtn.innerText = "Add Feature";
        addFeatBtn.addEventListener("click", () => {
          tier.features.push({ text: "New Feature", included: true });
          this.buildUI();
        });
        featList.appendChild(addFeatBtn);

        tierEdit.appendChild(featList);
        editArea.appendChild(tierEdit);
      });

      const addTierBtn = document.createElement("button");
      addTierBtn.classList.add("doclib-pr-add-btn");
      addTierBtn.innerText = "Add Pricing Tier";
      addTierBtn.addEventListener("click", () => {
        this.data.tiers.push({
          id: this.mkId(), name: "New Tier", price: "$99", period: "/mo",
          features: [{ text: "Feature 1", included: true }],
          recommended: false, btnText: "Select", btnUrl: "#", color: "#64748b"
        });
        this.buildUI();
      });

      editArea.appendChild(addTierBtn);
      this.wrapper.appendChild(editArea);
    }
  }

  save() {
    return this.data;
  }
}
