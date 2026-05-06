const https = require('https');
const packages = [
  "flipboxplus",
  "image-with-link",
  "header-with-alignment",
  "paragraph-with-alignment",
  "header-with-anchor",
  "simple-image-editorjs",
  "title-editorjs"
];

let count = packages.length;
packages.forEach(pkg => {
  https.get(`https://registry.npmjs.org/${encodeURIComponent(pkg)}`, res => {
    if (res.statusCode === 404) console.log(`${pkg} NOT FOUND`);
    count--;
  });
});
