import { API, BlockTool } from "@editorjs/editorjs";

export default class DocLibPricing implements BlockTool {
  private api: API;
  private wrapper: HTMLElement | null = null;
  private data: { 
    plans: { title: string, price: string, features: string[], highlighted: boolean }[] 
  };

  static get toolbox() {
    return {
      title: 'DocLib Pricing',
      icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
    };
  }

  static get isReadOnlySupported() { return true; }

  constructor({ api, data }: { api: API, data: any }) {
    this.api = api;
    this.data = {
      plans: data.plans && data.plans.length > 0 ? data.plans : [
          { title: 'Basic', price: '$0 / month', features: ['Feature 1', 'Feature 2'], highlighted: false },
          { title: 'Pro', price: '$9 / month', features: ['All basic features', 'VIP Feature'], highlighted: true }
      ]
    };
  }

  render() {
    this.wrapper = document.createElement('div');
    this.wrapper.classList.add(this.api.styles.block);
    
    if (!document.getElementById('doclib-pricing-styles')) {
        const style = document.createElement('style');
        style.id = 'doclib-pricing-styles';
        style.innerHTML = `
            .doclib-pr-wrapper { display: flex; gap: 16px; margin: 24px 0; align-items: stretch; justify-content: center; }
            .doclib-pr-card { flex: 1; min-width: 200px; max-width: 300px; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; background: #fff; text-align: center; position: relative; display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; }
            .doclib-pr-card:hover { transform: translateY(-4px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
            .doclib-pr-card.highlighted { border: 2px solid #3b82f6; box-shadow: 0 10px 15px -3px rgba(59,130,246,0.2); transform: scale(1.05); z-index: 10; }
            .doclib-pr-card.highlighted:hover { transform: scale(1.05) translateY(-4px); }
            .doclib-pr-badge { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
            .doclib-pr-title { font-size: 1.2em; font-weight: 700; color: #0f172a; margin-bottom: 8px; outline: none; }
            .doclib-pr-price { font-size: 1.8em; font-weight: 800; color: #3b82f6; margin-bottom: 24px; outline: none; }
            .doclib-pr-features { list-style: none; padding: 0; margin: 0 0 24px 0; flex-grow: 1; text-align: left; }
            .doclib-pr-feature { font-size: 0.95em; color: #475569; margin-bottom: 12px; display: flex; align-items: flex-start; gap: 8px; outline: none; }
            .doclib-pr-feature::before { content: ''; color: #10b981; font-weight: 700; }
            .doclib-pr-btn { width: 100%; padding: 12px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; border: none; }
            .doclib-pr-card .doclib-pr-btn { background: #f1f5f9; color: #0f172a; }
            .doclib-pr-card.highlighted .doclib-pr-btn { background: #3b82f6; color: white; }
            .doclib-pr-card .doclib-pr-btn:hover { background: #e2e8f0; }
            .doclib-pr-card.highlighted .doclib-pr-btn:hover { background: #2563eb; }
            .doclib-pr-controls { position: absolute; top: 8px; right: 8px; display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s; }
            .doclib-pr-card:hover .doclib-pr-controls { opacity: 1; }
            .doclib-pr-icon-btn { width: 24px; height: 24px; border-radius: 4px; border: none; background: #e2e8f0; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #475569; }
            .doclib-pr-icon-btn:hover { background: #cbd5e1; }
            .doclib-pr-add-col { flex: 0 0 auto; width: 40px; display: flex; align-items: center; justify-content: center; cursor: pointer; border: 2px dashed #cbd5e1; border-radius: 12px; color: #94a3b8; transition: border-color 0.2s, color 0.2s; }
            .doclib-pr-add-col:hover { border-color: #3b82f6; color: #3b82f6; }
        `;
        document.head.appendChild(style);
    }
    
    this.buildUI();
    return this.wrapper;
  }
  
  private buildUI() {
      if (!this.wrapper) return;
      this.wrapper.innerHTML = '';
      
      const container = document.createElement('div');
      container.classList.add('doclib-pr-wrapper');
      
      this.data.plans.forEach((plan, index) => {
          const card = document.createElement('div');
          card.classList.add('doclib-pr-card');
          if (plan.highlighted) card.classList.add('highlighted');
          
          if (plan.highlighted) {
              const badge = document.createElement('div');
              badge.classList.add('doclib-pr-badge');
              badge.innerText = 'Most Popular';
              card.appendChild(badge);
          }
          
          const title = document.createElement('div');
          title.classList.add('doclib-pr-title');
          title.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
          title.innerHTML = plan.title;
          title.addEventListener('input', () => plan.title = title.innerHTML);
          
          const price = document.createElement('div');
          price.classList.add('doclib-pr-price');
          price.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
          price.innerHTML = plan.price;
          price.addEventListener('input', () => plan.price = price.innerHTML);
          
          const featureList = document.createElement('ul');
          featureList.classList.add('doclib-pr-features');
          plan.features.forEach((feat, fIndex) => {
              const li = document.createElement('li');
              li.classList.add('doclib-pr-feature');
              li.contentEditable = !this.api.readOnly.toggle ? 'true' : 'false';
              li.innerHTML = feat;
              li.addEventListener('input', () => plan.features[fIndex] = li.innerHTML);
              li.addEventListener('keydown', (e) => {
                  if (e.key === 'Enter') {
                      e.preventDefault();
                      plan.features.splice(fIndex + 1, 0, 'New feature');
                      this.buildUI();
                  } else if (e.key === 'Backspace' && li.innerHTML === '') {
                      e.preventDefault();
                      plan.features.splice(fIndex, 1);
                      this.buildUI();
                  }
              });
              featureList.appendChild(li);
          });
          
          if (!this.api.readOnly.toggle && plan.features.length === 0) {
              const addF = document.createElement('li');
              addF.classList.add('doclib-pr-feature');
              addF.style.cursor = 'pointer';
              addF.style.opacity = '0.5';
              addF.innerText = '+ Add feature';
              addF.addEventListener('click', () => {
                  plan.features.push('New feature');
                  this.buildUI();
              });
              featureList.appendChild(addF);
          }
          
          const ctaBtn = document.createElement('button');
          ctaBtn.classList.add('doclib-pr-btn');
          ctaBtn.innerText = 'Subscribe now';
          
          card.appendChild(title);
          card.appendChild(price);
          card.appendChild(featureList);
          card.appendChild(ctaBtn);
          
          if (!this.api.readOnly.toggle) {
              const controls = document.createElement('div');
              controls.classList.add('doclib-pr-controls');
              
              const starBtn = document.createElement('button');
              starBtn.classList.add('doclib-pr-icon-btn');
              starBtn.innerHTML = plan.highlighted ? '' : '';
              starBtn.title = 'Highlight';
              starBtn.addEventListener('click', () => {
                  this.data.plans.forEach(p => p.highlighted = false);
                  plan.highlighted = true;
                  this.buildUI();
              });
              
              const rmBtn = document.createElement('button');
              rmBtn.classList.add('doclib-pr-icon-btn');
              rmBtn.innerHTML = '&times;';
              rmBtn.title = 'Delete this plan';
              rmBtn.addEventListener('click', () => {
                  this.data.plans.splice(index, 1);
                  this.buildUI();
              });
              
              controls.appendChild(starBtn);
              if (this.data.plans.length > 1) controls.appendChild(rmBtn);
              card.appendChild(controls);
          }
          
          container.appendChild(card);
      });
      
      if (!this.api.readOnly.toggle && this.data.plans.length < 4) {
          const addCol = document.createElement('div');
          addCol.classList.add('doclib-pr-add-col');
          addCol.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>';
          addCol.title = 'Add New Plan';
          addCol.addEventListener('click', () => {
              this.data.plans.push({ title: 'New Plan', price: '$0', features: ['Feature 1'], highlighted: false });
              this.buildUI();
          });
          container.appendChild(addCol);
      }
      
      this.wrapper.appendChild(container);
  }

  save() { return this.data; }
}
