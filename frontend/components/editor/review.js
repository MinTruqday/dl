const fs = require('fs');
const files = [
  'DocLibAiText.ts', 'DocLibAlert.ts', 'DocLibAlignment.ts', 'DocLibAnchor.ts', 'DocLibAnnotation.ts', 'DocLibAudio.ts', 'DocLibAudioPlayer.ts',
  'DocLibBadge.ts', 'DocLibBookmark.ts', 'DocLibBreakLine.ts', 'DocLibButton.ts',
  'DocLibCallout.ts', 'DocLibCarousel.ts', 'DocLibChangeCase.ts', 'DocLibChart.ts', 'DocLibChecklist.ts', 'DocLibCode.ts', 'DocLibCodeBox.ts', 'DocLibCodeMirror.ts', 'DocLibColumns.ts', 'DocLibComment.ts', 'DocLibCountdown.ts'
];

for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');
  let issues = [];
  
  if (content.includes('...')) issues.push('Contains ...');
  if (content.match(/[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]/) && content.match(/[àáãạảăắằẳẵặâấầẩẫậèéẹẻẽêềếểễệđìíĩỉịòóõọỏôốồổỗộơớờởỡợùúúũụủưứừửữựỳỵỷỹý]/i)) issues.push('Contains Vietnamese');
  
  if (issues.length > 0) {
    console.log(`\n--- ${file} ---`);
    console.log(issues.join(', '));
  }
}
