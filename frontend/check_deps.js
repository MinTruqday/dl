const { execSync } = require('child_process');
const fs = require('fs');

const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const deps = pkg.dependencies;
const toCheck = Object.keys(deps).filter(d => d.includes('editorjs') || d.includes('editor-js') || d.includes('header-with') || d.includes('paragraph-with') || d.includes('title-editorjs') || d.includes('simple-image-editorjs') || d.includes('flipboxplus') || d.includes('image-with-link'));

toCheck.forEach(d => {
  try {
    execSync(`npm view ${d} name`, { stdio: 'ignore' });
    // console.log(`${d} OK`);
  } catch (e) {
    console.log(`${d} MISSING`);
  }
});
