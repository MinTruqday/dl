const fs = require('fs');
const files = [
  'DocLibAiText.ts', 'DocLibAlert.ts', 'DocLibAlignment.ts', 'DocLibAnchor.ts', 'DocLibAnnotation.ts', 'DocLibAudio.ts', 'DocLibAudioPlayer.ts',
  'DocLibBadge.ts', 'DocLibBookmark.ts', 'DocLibBreakLine.ts', 'DocLibButton.ts',
  'DocLibCallout.ts', 'DocLibCarousel.ts', 'DocLibChangeCase.ts', 'DocLibChart.ts', 'DocLibChecklist.ts', 'DocLibCode.ts', 'DocLibCodeBox.ts', 'DocLibCodeMirror.ts', 'DocLibColumns.ts', 'DocLibComment.ts', 'DocLibCountdown.ts'
];

const dict = {
  'Bạn muốn tôi viết gì? (VD: Viết một đoạn văn tóm tắt)': 'Enter AI prompt',
  'Create nội dung': 'Generate Content',
  'Đang viết': 'Generating',
  'Dưới đây là nội dung AI đã tạo theo yêu cầu:\\n\\n': '',
  '\\n\\nBạn có thể chỉnh sửa trực tiếp đoạn văn bản này để hoàn thiện nội dung. (Tính năng này đang được mock kết quả, vui lòng kết nối API backend thực tế để AI hoạt động).': '',
  'DocLib AI đang suy nghĩ và soạn thảo nội dung': 'AI is generating content',
  'Neo thẻ (Anchor)': 'Anchor',
  'Thêm chú thích': 'Add caption',
  'Nhập chú thích audio': 'Enter audio caption',
  'Tiêu đề trang': 'Page title',
  'Vui lòng nhập đầy đủ Tên nút và Đường link!': 'Please enter button text and link',
  '+ Thêm Ảnh': '+ Add Image',
  'Nhập URL ảnh mới:': 'Enter new image URL:',
  '- Delete Image Này': '- Delete Image',
  'Delete ảnh này khỏi Carousel?': 'Delete image from Carousel?',
  'Nhập URL ảnh đầu tiên cho Carousel': 'Enter first image URL',
  'Tháng 1': 'Jan',
  'Tháng 2': 'Feb',
  'Tháng 3': 'Mar',
  'Nhãn (X)': 'Label (X)',
  '+ Thêm Dòng (Trục X)': '+ Add Row',
  'Nhãn mới': 'New label',
  '+ Thêm Cột (Dataset)': '+ Add Dataset',
  'Dataset mới': 'New dataset',
  '- Delete Dòng Cuối': '- Delete Last Row',
  'Nhập nội dung': 'Enter text',
  'Nhập nội dung cột': 'Enter column text',
  'Cột`': 'Columns`',
  'Nhập bình luận/Note': 'Enter comment/note',
  'Bình luận mới': 'New comment',
  '💡': '', '⚠️': '', '🔥': '', '📝': '', '📌': '', '🎉': '', '🚀': '', '✅': '', '❌': '', '✨': '', '🤖': '', '📷': '', '🎵': '', '🔗': '', '💬': '' // Stripping emojis
};

const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu;

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  
  for (const [vi, en] of Object.entries(dict)) {
    content = content.split(vi).join(en);
  }
  
  // Remove emojis
  content = content.replace(emojiRegex, '');
  
  fs.writeFileSync(file, content, 'utf8');
}

console.log('Cleaned up Vietnamese text and Emojis successfully!');
