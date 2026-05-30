const fs = require('fs');

const files = [
  'DocLibAiText.ts', 'DocLibAlert.ts', 'DocLibAlignment.ts', 'DocLibAnchor.ts', 'DocLibAnnotation.ts', 'DocLibAudio.ts', 'DocLibAudioPlayer.ts',
  'DocLibBadge.ts', 'DocLibBookmark.ts', 'DocLibBreakLine.ts', 'DocLibButton.ts',
  'DocLibCallout.ts', 'DocLibCarousel.ts', 'DocLibChangeCase.ts', 'DocLibChart.ts', 'DocLibChecklist.ts', 'DocLibCode.ts', 'DocLibCodeBox.ts', 'DocLibCodeMirror.ts', 'DocLibColumns.ts', 'DocLibComment.ts', 'DocLibCountdown.ts'
];

const dict = {
  'Nhập nội dung nổi bật...': 'Enter highlight text',
  'Nhập Emoji mới:': 'Enter new icon:',
  'Tiêu đề trang web...': 'Web page title',
  'Mô tả ngắn...': 'Short description',
  'Đổi ảnh': 'Change image',
  'URL Ảnh Preview:': 'Preview Image URL:',
  'Dán Link Web Bookmark...': 'Paste Web Bookmark Link',
  'Tạo': 'Create',
  'Sự kiện sắp tới': 'Upcoming Event',
  'Ngày': 'Days',
  'Giờ': 'Hours',
  'Phút': 'Minutes',
  'Giây': 'Seconds',
  'Tiến độ dự án': 'Project progress',
  'Bước 1': 'Step 1',
  'Bước 2': 'Step 2',
  'Mô tả chi tiết bước 1': 'Detailed step description 1',
  'Nhập tiêu đề bước...': 'Enter step title',
  'Nhập mô tả chi tiết...': 'Enter detailed description',
  '+ Thêm Bước': '+ Add Step',
  'Nhập câu hỏi khảo sát...': 'Enter survey question',
  'Lựa chọn 1': 'Option 1',
  'Lựa chọn 2': 'Option 2',
  'Nhập lựa chọn...': 'Enter option',
  '+ Thêm Lựa chọn': '+ Add Option',
  'Nhúng (Embed)': 'Embed',
  'Độ cao:': 'Height:',
  'Nhập độ cao (px):': 'Enter height (px):',
  'Đổi Link': 'Change Link',
  'Dán Link nhúng (CodePen, CodeSandbox, Figma, Typeform, v.v...)': 'Paste embed link',
  'Nhập văn bản (Tạo text bằng AI)...': 'Enter text (AI Prompt)',
  'Nhập văn bản (Tạo text bằng AI)': 'Enter text (AI Prompt)',
  'Nhập tiêu đề...': 'Enter title',
  'Nhập tiêu đề': 'Enter title',
  'Nhập thông báo...': 'Enter notice',
  'Cảnh báo': 'Warning',
  'Chèn Link': 'Insert Link',
  'Chèn': 'Insert',
  'Nhập link file Audio (VD: .mp3, .wav)...': 'Enter audio link (.mp3, .wav)',
  'Tên bài hát/Podcast...': 'Song/Podcast Title',
  'Tên ca sĩ/Tác giả...': 'Artist/Author Name',
  'Tạo Audio Player': 'Create Audio Player',
  'Nhập URL ảnh bìa (Cover Art):': 'Enter Cover Art URL:',
  'Dán URL file Audio (.mp3, .wav)...': 'Paste Audio URL (.mp3, .wav)',
  'Thành công': 'Success',
  'Thông tin': 'Info',
  'Cảnh báo': 'Warning',
  'Lỗi': 'Error',
  'Nhập nội dung cảnh báo/lưu ý...': 'Enter alert message',
  'Nội dung Neo (Mặc định: neo-123)...': 'Anchor ID (e.g. anchor-123)',
  'Liên kết tĩnh (Anchor)': 'Anchor Link',
  'Ghi chú ẩn (Annotation)...': 'Hidden Annotation',
  'Nhập văn bản nút...': 'Enter button text',
  'Dán Link đích...': 'Paste destination link',
  'Thêm Hình ảnh...': 'Add Images',
  'Xóa Ảnh': 'Delete Image',
  'Loại Biểu đồ:': 'Chart Type:',
  'Nhập tên nhãn (ngăn cách bằng dấu phẩy)...': 'Enter labels (comma separated)',
  'Dữ liệu': 'Data',
  'Thêm Dữ liệu': 'Add Data',
  'Nhập tên...': 'Enter name',
  'Giá trị': 'Values',
  'Thêm Mục': 'Add Item',
  'Nhập mã nguồn...': 'Enter source code',
  'Nhập mã nguồn vào đây...': 'Enter source code here',
  'Tên File / Tiêu đề...': 'File Name / Title',
  'Cột 1': 'Column 1',
  'Cột 2': 'Column 2',
  'Nội dung bình luận...': 'Comment text',
  'Người đăng': 'Author',
  'Nhập tên tác giả...': 'Enter author name',
  'Chèn Code': 'Insert Code',
  'Thêm Code': 'Add Code',
  'Nhập Code...': 'Enter code',
  'Văn bản AI...': 'AI Text',
  'Nhập ghi chú...': 'Enter note',
  'Thay thế': 'Replace',
  'Đã lưu': 'Saved',
  'Ghi chú': 'Note',
  'Xóa': 'Delete',
  'Lưu': 'Save',
  'Hủy': 'Cancel',
  'Mô tả...': 'Description',
  'Mô tả': 'Description'
};

for (const file of files) {
  let content = fs.readFileSync(file, 'utf8');
  
  // 1. Replace mapped words
  for (const [vi, en] of Object.entries(dict)) {
    content = content.split(vi).join(en);
  }
  
  // 2. Remove ellipses "..." inside strings (be careful not to break spread operators)
  content = content.replace(/(['"`])([^'"`]*)\.\.\.([^'"`]*)(['"`])/g, '$1$2$3$4');
  
  // 3. Strip // comments EXCEPT URLs like http:// or https://
  content = content.replace(/(?<!https?:)\/\/.*$/gm, '');

  fs.writeFileSync(file, content, 'utf8');
}
console.log('Translated successfully!');
