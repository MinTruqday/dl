const fs = require('fs');
const files = fs.readdirSync('.').filter(f => f.startsWith('DocLib') && f.endsWith('.ts'));

const viRegex = /[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]/;
const viRegex2 = /[àáãạảăắằẳẵặâấầẩẫậèéẹẻẽêềếểễệđìíĩỉịòóõọỏôốồổỗộơớờởỡợùúũụủưứừửữựỳỵỷỹý]/i;

const strings = new Set();
for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');
  const matches = content.match(/['"`](.*?)['"`]/g);
  if (matches) {
    for (const match of matches) {
      if (viRegex.test(match) && viRegex2.test(match)) {
        strings.add(match);
      }
    }
  }
}
fs.writeFileSync('vi_strings_all.json', JSON.stringify(Array.from(strings), null, 2));
console.log('Extracted ' + strings.size + ' strings from ' + files.length + ' files.');
