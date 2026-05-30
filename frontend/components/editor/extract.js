const fs = require('fs');
const files = [
  'DocLibAiText.ts', 'DocLibAlert.ts', 'DocLibAlignment.ts', 'DocLibAnchor.ts', 'DocLibAnnotation.ts', 'DocLibAudio.ts', 'DocLibAudioPlayer.ts',
  'DocLibBadge.ts', 'DocLibBookmark.ts', 'DocLibBreakLine.ts', 'DocLibButton.ts',
  'DocLibCallout.ts', 'DocLibCarousel.ts', 'DocLibChangeCase.ts', 'DocLibChart.ts', 'DocLibChecklist.ts', 'DocLibCode.ts', 'DocLibCodeBox.ts', 'DocLibCodeMirror.ts', 'DocLibColumns.ts', 'DocLibComment.ts', 'DocLibCountdown.ts'
];
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
fs.writeFileSync('vi_strings.json', JSON.stringify(Array.from(strings), null, 2));
console.log('Extracted ' + strings.size + ' strings');
