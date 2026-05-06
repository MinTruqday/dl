const https = require('https');
const packages = [
  "@bomdi/codebox",
  "@calumk/editorjs-codeflask",
  "@calumk/editorjs-columns",
  "@calumk/editorjs-nested-checklist",
  "@coolbytes/editorjs-anchor",
  "@coolbytes/editorjs-delimiter",
  "@cychann/editorjs-group-image",
  "@cychann/editorjs-quote",
  "@furison-tech/editorjs-audio",
  "@rxpm/editor-js-code",
  "@skchawala/editorjs-text-style",
  "@sotaproject/strikethrough",
  "@volgaigor/editorjs-anchor",
  "@volgaigor/editorjs-annotation",
  "@volgaigor/editorjs-gallery",
  "@volgaigor/editorjs-notice"
];

packages.forEach(pkg => {
  https.get(`https://registry.npmjs.org/${encodeURIComponent(pkg)}`, res => {
    if (res.statusCode === 404) console.log(`${pkg} NOT FOUND`);
    else console.log(`${pkg} OK`);
  });
});
