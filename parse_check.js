const fs = require('fs');
const acorn = require('acorn');
const jsx = require('acorn-jsx');

const code = fs.readFileSync('frontend/app/(main)/luu-tru/page.tsx', 'utf8');

try {
  acorn.Parser.extend(jsx()).parse(code, { sourceType: 'module', ecmaVersion: 2020 });
  console.log("No syntax errors found by acorn-jsx");
} catch (e) {
  console.error("Syntax error:", e.message);
}
