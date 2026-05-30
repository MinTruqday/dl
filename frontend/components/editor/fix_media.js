const fs = require('fs');

const uiTemplate = (type, title, desc, iconSvg) => `
          const uploader = document.createElement('label');
          uploader.style.display = 'flex';
          uploader.style.flexDirection = 'column';
          uploader.style.alignItems = 'center';
          uploader.style.justifyContent = 'center';
          uploader.style.border = '2px dashed #cbd5e1';
          uploader.style.borderRadius = '12px';
          uploader.style.padding = '32px';
          uploader.style.background = '#f8fafc';
          uploader.style.cursor = 'pointer';
          uploader.style.color = '#475569';
          uploader.innerHTML = \`
              <div style="color: #94a3b8; margin-bottom: 12px;">${iconSvg}</div>
              <div style="font-weight: 500; font-size: 1.1em; margin-bottom: 4px;">${title}</div>
              <div style="font-size: 0.9em; opacity: 0.8;">${desc}</div>
          \`;
          
          const fileInput = document.createElement('input');
          fileInput.type = 'file';
          fileInput.style.display = 'none';
          
          fileInput.addEventListener('change', () => {
              if (fileInput.files && fileInput.files[0]) {
                  const file = fileInput.files[0];
                  const formData = new FormData();
                  formData.append('file', file);
                  const endpoint = this.config?.endpoints?.byFile || '/api/uploadFile';
                  
                  uploader.innerHTML = '<div style="padding: 20px; font-weight: 500;">Uploading...</div>';
                  
                  fetch(endpoint, { method: 'POST', body: formData })
                  .then(res => res.json())
                  .then(res => {
                      if (res.success === 1 && res.file && res.file.url) {
                          this.data.url = res.file.url;
                          ${type === 'file' ? 'this.data.file = { url: res.file.url, name: file.name, size: file.size, extension: file.name.split(".").pop().toUpperCase() }; this.data.title = file.name;' : ''}
                      } else {
                          this.data.url = res.url || res.data?.url || URL.createObjectURL(file);
                          ${type === 'file' ? 'this.data.file = { url: this.data.url, name: file.name, size: file.size, extension: file.name.split(".").pop().toUpperCase() }; this.data.title = file.name;' : ''}
                      }
                      this.buildUI();
                  })
                  .catch(err => {
                      console.error("Upload failed", err);
                      this.data.url = URL.createObjectURL(file);
                      ${type === 'file' ? 'this.data.file = { url: this.data.url, name: file.name, size: file.size, extension: file.name.split(".").pop().toUpperCase() }; this.data.title = file.name;' : ''}
                      this.buildUI();
                  });
              }
          });
          
          uploader.appendChild(fileInput);
          
          uploader.addEventListener('contextmenu', (e) => {
              e.preventDefault();
              const url = prompt('Paste direct URL:');
              if (url) {
                  this.data.url = url;
                  ${type === 'file' ? 'this.data.file = { url, name: url.split("/").pop(), size: 0, extension: "FILE" }; this.data.title = url.split("/").pop();' : ''}
                  this.buildUI();
              }
          });
          this.wrapper.appendChild(uploader);
`;

const configs = [
    {
        file: 'DocLibAudio.ts',
        type: 'audio',
        targetRegex: /const container = document.createElement\('div'\);[\s\S]*?this\.wrapper\.appendChild\(container\);\s*\}/,
        title: 'Upload Audio',
        desc: 'Click to select file or Right click to paste URL',
        icon: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>'
    },
    {
        file: 'DocLibVideo.ts',
        type: 'video',
        targetRegex: /const container = document.createElement\('div'\);[\s\S]*?this\.wrapper\.appendChild\(container\);\s*\}/,
        title: 'Upload Video',
        desc: 'Click to select file or Right click to paste URL',
        icon: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>'
    },
    {
        file: 'DocLibFile.ts',
        type: 'file',
        targetRegex: /const container = document.createElement\('div'\);[\s\S]*?this\.wrapper\.appendChild\(container\);\s*\}/,
        title: 'Upload Attachment',
        desc: 'Click to select file or Right click to paste URL',
        icon: '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>'
    }
];

for (const c of configs) {
    let content = fs.readFileSync(c.file, 'utf8');
    
    // Add config property
    if (!content.includes('private config: any;')) {
        content = content.replace('private data:', 'private config: any;\n  private data:');
    }
    if (!content.includes('this.config = config;')) {
        content = content.replace('constructor({ api, data }', 'constructor({ api, data, config }');
        content = content.replace('this.api = api;', 'this.api = api;\n    this.config = config || {};');
    }
    
    const replacement = uiTemplate(c.type, c.title, c.desc, c.icon) + ' }';
    content = content.replace(c.targetRegex, replacement);
    
    fs.writeFileSync(c.file, content, 'utf8');
    console.log('Fixed ' + c.file);
}
