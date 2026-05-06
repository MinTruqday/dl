const https = require('https');
const fs = require('fs');

const pkg = JSON.parse(fs.readFileSync('./frontend/package.json', 'utf8'));
const deps = Object.keys(pkg.dependencies).filter(d => d.includes('editorjs') || d.includes('editor-js'));

let count = deps.length;
let missing = [];

deps.forEach(d => {
  https.get(`https://registry.npmjs.org/${encodeURIComponent(d)}`, res => {
    if (res.statusCode === 404) {
      missing.push(d);
    }
    count--;
    if (count === 0) {
      console.log("MISSING_PACKAGES:");
      missing.forEach(m => console.log(m));
    }
  });
});
