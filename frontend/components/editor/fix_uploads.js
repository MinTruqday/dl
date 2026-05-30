const fs = require('fs');

function fixFile(filename) {
    let content = fs.readFileSync(filename, 'utf8');

    // 1. Ensure config is in constructor
    if (!content.includes('private config: any;')) {
        content = content.replace('private data:', 'private config: any;\n  private data:');
    }
    if (!content.includes('this.config = config;')) {
        content = content.replace('constructor({ api, data }', 'constructor({ api, data, config }');
        content = content.replace('this.api = api;', 'this.api = api;\n    this.config = config || {};');
    }

    // 2. Replace URL.createObjectURL with fetch upload
    // The exact string depends on the file.
    
    // For DocLibImage.ts
    if (filename.includes('DocLibImage.ts')) {
        const target = `const url = URL.createObjectURL(input.files[0]);
                  this.data.file.url = url;
                  this.buildUI();`;
        
        const replacement = `const file = input.files[0];
                  const formData = new FormData();
                  formData.append('file', file);
                  
                  const endpoint = this.config.endpoints?.byFile || '/api/uploadFile';
                  
                  // Show uploading state (simple text change)
                  uploader.innerHTML = '<div style="padding: 20px; font-weight: 500;">Uploading...</div>';
                  
                  fetch(endpoint, {
                      method: 'POST',
                      body: formData
                  })
                  .then(res => res.json())
                  .then(res => {
                      if (res.success === 1 && res.file && res.file.url) {
                          this.data.file.url = res.file.url;
                      } else {
                          // Fallback if backend doesn't match EditorJS format
                          this.data.file.url = res.url || res.data?.url || URL.createObjectURL(file);
                      }
                      this.buildUI();
                  })
                  .catch(err => {
                      console.error("Upload failed", err);
                      this.data.file.url = URL.createObjectURL(file);
                      this.buildUI();
                  });`;
                  
        content = content.replace(target, replacement);
        
        // Also fix translation for 'Tải ảnh lên' and 'Click để chọn file hoặc Click chuột phải để dán URL'
        content = content.replace('Tải ảnh lên', 'Upload Image');
        content = content.replace('Click để chọn file hoặc Click chuột phải để dán URL', 'Click to select file or Right click to paste URL');
    }
    
    fs.writeFileSync(filename, content, 'utf8');
}

fixFile('DocLibImage.ts');
console.log('Fixed DocLibImage.ts');
