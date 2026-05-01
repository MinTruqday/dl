from typing import Any
from core.response import APIResponse

LATEX_PACKAGES = [
    {
        "label": "amsmath",
        "insertText": "amsmath",
        "detail": "Gói hỗ trợ soạn thảo công thức toán học nâng cao",
        "type": "snippet"
    },
    {
        "label": "mathtools",
        "insertText": "mathtools",
        "detail": "Cung cấp các công cụ toán học bổ sung và sửa lỗi amsmath",
        "type": "snippet"
    },
    {
        "label": "amssymb",
        "insertText": "amssymb",
        "detail": "Chèn các ký hiệu toán học bổ sung từ AMS",
        "type": "snippet"
    },
    {
        "label": "amsthm",
        "insertText": "amsthm",
        "detail": "Tạo các môi trường định lý, hệ quả, chứng minh",
        "type": "snippet"
    },
    {
        "label": "geometry",
        "insertText": "geometry",
        "detail": "Thiết lập lề trang và kích thước giấy",
        "type": "snippet"
    },
    {
        "label": "graphicx",
        "insertText": "graphicx",
        "detail": "Chèn và xử lý hình ảnh",
        "type": "snippet"
    },
    {
        "label": "xcolor",
        "insertText": "xcolor",
        "detail": "Hỗ trợ sử dụng và định nghĩa màu sắc",
        "type": "snippet"
    },
    {
        "label": "hyperref",
        "insertText": "hyperref",
        "detail": "Tạo liên kết nội bộ và liên kết web (URL)",
        "type": "snippet"
    },
    {
        "label": "cleveref",
        "insertText": "cleveref",
        "detail": "Trích dẫn thông minh tự động nhận diện loại đối tượng",
        "type": "snippet"
    },
    {
        "label": "biblatex",
        "insertText": "biblatex",
        "detail": "Quản lý và trích dẫn tài liệu tham khảo hiện đại",
        "type": "snippet"
    },
    {
        "label": "siunitx",
        "insertText": "siunitx",
        "detail": "Định dạng số và đơn vị đo lường theo chuẩn SI",
        "type": "snippet"
    },
    {
        "label": "chemfig",
        "insertText": "chemfig",
        "detail": "Vẽ cấu trúc hóa học và liên kết phân tử",
        "type": "snippet"
    },
    {
        "label": "mhchem",
        "insertText": "mhchem",
        "detail": "Viết công thức hóa học nhanh chóng",
        "type": "snippet"
    },
    {
        "label": "tikz",
        "insertText": "tikz",
        "detail": "Công cụ vẽ hình đồ họa vector chuyên nghiệp",
        "type": "snippet"
    },
    {
        "label": "pgfplots",
        "insertText": "pgfplots",
        "detail": "Vẽ biểu đồ và đồ thị hàm số từ dữ liệu",
        "type": "snippet"
    },
    {
        "label": "algorithm2e",
        "insertText": "algorithm2e",
        "detail": "Soạn thảo thuật toán với cấu trúc rõ ràng",
        "type": "snippet"
    },
    {
        "label": "listings",
        "insertText": "listings",
        "detail": "Chèn mã nguồn chương trình với định dạng màu",
        "type": "snippet"
    },
    {
        "label": "tcolorbox",
        "insertText": "tcolorbox",
        "detail": "Tạo khung màu trang trí và hộp văn bản",
        "type": "snippet"
    },
    {
        "label": "enumitem",
        "insertText": "enumitem",
        "detail": "Tùy chỉnh danh sách liệt kê và mô tả",
        "type": "snippet"
    },
    {
        "label": "booktabs",
        "insertText": "booktabs",
        "detail": "Tạo bảng chuyên nghiệp với đường kẻ chuẩn",
        "type": "snippet"
    },
    {
        "label": "tabularray",
        "insertText": "tabularray",
        "detail": "Soạn thảo bảng hiện đại và linh hoạt",
        "type": "snippet"
    },
    {
        "label": "beamer",
        "insertText": "beamer",
        "detail": "Tạo bài thuyết trình (slides) chuyên nghiệp",
        "type": "snippet"
    },
    {
        "label": "caption",
        "insertText": "caption",
        "detail": "Tùy chỉnh tiêu đề cho hình ảnh và bảng biểu",
        "type": "snippet"
    },
    {
        "label": "float",
        "insertText": "float",
        "detail": "Điều khiển vị trí các đối tượng nổi",
        "type": "snippet"
    },
    {
        "label": "fancyhdr",
        "insertText": "fancyhdr",
        "detail": "Thiết lập tiêu đề đầu trang và chân trang",
        "type": "snippet"
    },
]

LATEX_COMMANDS = [
    {
        "label": "\\documentclass[options]{class}",
        "insertText": "\\documentclass[${1:options}]{${2:class}}",
        "detail": "Khai báo loại tài liệu",
        "type": "snippet"
    },
    {
        "label": "\\usepackage[options]{package}",
        "insertText": "\\usepackage[${1:options}]{${2:package}}",
        "detail": "Khai báo sử dụng gói lệnh",
        "type": "snippet"
    },
    {
        "label": "\\title{title}",
        "insertText": "\\title{${1:title}}",
        "detail": "Thiết lập tiêu đề tài liệu",
        "type": "snippet"
    },
    {
        "label": "\\author{name}",
        "insertText": "\\author{${1:name}}",
        "detail": "Thiết lập tên tác giả",
        "type": "snippet"
    },
    {
        "label": "\\date{date}",
        "insertText": "\\date{${1:date}}",
        "detail": "Thiết lập ngày tháng",
        "type": "snippet"
    },
    {
        "label": "\\maketitle",
        "insertText": "\\maketitle",
        "detail": "Tạo trang tiêu đề",
        "type": "snippet"
    },
    {
        "label": "\\tableofcontents",
        "insertText": "\\tableofcontents",
        "detail": "Tạo mục lục",
        "type": "snippet"
    },
    {
        "label": "\\section{title}",
        "insertText": "\\section{${1:title}}",
        "detail": "Tạo mục chính",
        "type": "snippet"
    },
    {
        "label": "\\subsection{title}",
        "insertText": "\\subsection{${1:title}}",
        "detail": "Tạo mục phụ",
        "type": "snippet"
    },
    {
        "label": "\\subsubsection{title}",
        "insertText": "\\subsubsection{${1:title}}",
        "detail": "Tạo mục phụ cấp 2",
        "type": "snippet"
    },
    {
        "label": "\\paragraph{title}",
        "insertText": "\\paragraph{${1:title}}",
        "detail": "Tạo đoạn văn có tiêu đề",
        "type": "snippet"
    },
    {
        "label": "\\chapter{title}",
        "insertText": "\\chapter{${1:title}}",
        "detail": "Tạo chương mới",
        "type": "snippet"
    },
    {
        "label": "\\part{title}",
        "insertText": "\\part{${1:title}}",
        "detail": "Tạo phần mới",
        "type": "snippet"
    },
    {
        "label": "\\textbf{text}",
        "insertText": "\\textbf{${1:text}}",
        "detail": "Định dạng in đậm văn bản",
        "type": "snippet"
    },
    {
        "label": "\\textit{text}",
        "insertText": "\\textit{${1:text}}",
        "detail": "Định dạng in nghiêng văn bản",
        "type": "snippet"
    },
    {
        "label": "\\underline{text}",
        "insertText": "\\underline{${1:text}}",
        "detail": "Định dạng gạch chân văn bản",
        "type": "snippet"
    },
    {
        "label": "\\emph{text}",
        "insertText": "\\emph{${1:text}}",
        "detail": "Định dạng nhấn mạnh văn bản",
        "type": "snippet"
    },
    {
        "label": "\\textsf{text}",
        "insertText": "\\textsf{${1:text}}",
        "detail": "Định dạng phông không chân",
        "type": "snippet"
    },
    {
        "label": "\\texttt{text}",
        "insertText": "\\texttt{${1:text}}",
        "detail": "Định dạng phông đánh máy",
        "type": "snippet"
    },
    {
        "label": "\\textsc{text}",
        "insertText": "\\textsc{${1:text}}",
        "detail": "Định dạng chữ hoa nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\centering",
        "insertText": "\\centering",
        "detail": "Căn giữa nội dung",
        "type": "snippet"
    },
    {
        "label": "\\raggedright",
        "insertText": "\\raggedright",
        "detail": "Căn lề trái",
        "type": "snippet"
    },
    {
        "label": "\\raggedleft",
        "insertText": "\\raggedleft",
        "detail": "Căn lề phải",
        "type": "snippet"
    },
    {
        "label": "\\label{key}",
        "insertText": "\\label{${1:label}}",
        "detail": "Đặt nhãn tham chiếu",
        "type": "snippet"
    },
    {
        "label": "\\ref{key}",
        "insertText": "\\ref{${1:label}}",
        "detail": "Tham chiếu đến nhãn",
        "type": "snippet"
    },
    {
        "label": "\\pageref{key}",
        "insertText": "\\pageref{${1:label}}",
        "detail": "Tham chiếu đến số trang",
        "type": "snippet"
    },
    {
        "label": "\\cite{key}",
        "insertText": "\\cite{${1:key}}",
        "detail": "Trích dẫn tài liệu tham khảo",
        "type": "snippet"
    },
    {
        "label": "\\footnote{text}",
        "insertText": "\\footnote{${1:text}}",
        "detail": "Chèn chú thích chân trang",
        "type": "snippet"
    },
    {
        "label": "\\href{url}{text}",
        "insertText": "\\href{${1:url}}{${2:text}}",
        "detail": "Chèn liên kết web",
        "type": "snippet"
    },
    {
        "label": "\\url{url}",
        "insertText": "\\url{${1:url}}",
        "detail": "Chèn địa chỉ URL",
        "type": "snippet"
    },
    {
        "label": "\\frac{num}{den}",
        "insertText": "\\frac{${1:num}}{${2:den}}",
        "detail": "Chèn phân số",
        "type": "snippet"
    },
    {
        "label": "\\sqrt{val}",
        "insertText": "\\sqrt{${1:value}}",
        "detail": "Chèn căn bậc hai",
        "type": "snippet"
    },
    {
        "label": "\\sum_{i=1}^{n}",
        "insertText": "\\sum_{${1:i=1}}^{${2:n}} ${3:a_i}",
        "detail": "Chèn tổng Sigma",
        "type": "snippet"
    },
    {
        "label": "\\int_{a}^{b}",
        "insertText": "\\int_{${1:a}}^{${2:b}} ${3:f(x)} dx",
        "detail": "Chèn tích phân",
        "type": "snippet"
    },
    {
        "label": "\\limit_{x \\to a}",
        "insertText": "\\lim_{${1:x \\to a}} ${2:f(x)}",
        "detail": "Chèn giới hạn",
        "type": "snippet"
    },
    {
        "label": "\\color{red}",
        "insertText": "\\color{red}",
        "detail": "Thiết lập màu red",
        "type": "snippet"
    },
    {
        "label": "\\color{blue}",
        "insertText": "\\color{blue}",
        "detail": "Thiết lập màu blue",
        "type": "snippet"
    },
    {
        "label": "\\color{green}",
        "insertText": "\\color{green}",
        "detail": "Thiết lập màu green",
        "type": "snippet"
    },
    {
        "label": "\\color{black}",
        "insertText": "\\color{black}",
        "detail": "Thiết lập màu black",
        "type": "snippet"
    },
    {
        "label": "\\color{white}",
        "insertText": "\\color{white}",
        "detail": "Thiết lập màu white",
        "type": "snippet"
    },
    {
        "label": "\\color{gray}",
        "insertText": "\\color{gray}",
        "detail": "Thiết lập màu gray",
        "type": "snippet"
    },
    {
        "label": "\\color{yellow}",
        "insertText": "\\color{yellow}",
        "detail": "Thiết lập màu yellow",
        "type": "snippet"
    },
    {
        "label": "\\color{orange}",
        "insertText": "\\color{orange}",
        "detail": "Thiết lập màu orange",
        "type": "snippet"
    },
    {
        "label": "\\color{purple}",
        "insertText": "\\color{purple}",
        "detail": "Thiết lập màu purple",
        "type": "snippet"
    },
    {
        "label": "\\color{brown}",
        "insertText": "\\color{brown}",
        "detail": "Thiết lập màu brown",
        "type": "snippet"
    },
    {
        "label": "\\alpha",
        "insertText": "\\alpha",
        "detail": "Chèn ký hiệu Alpha",
        "type": "snippet"
    },
    {
        "label": "\\Alpha",
        "insertText": "\\Alpha",
        "detail": "Chèn ký hiệu Alpha hoa",
        "type": "snippet"
    },
    {
        "label": "\\beta",
        "insertText": "\\beta",
        "detail": "Chèn ký hiệu Beta",
        "type": "snippet"
    },
    {
        "label": "\\Beta",
        "insertText": "\\Beta",
        "detail": "Chèn ký hiệu Beta hoa",
        "type": "snippet"
    },
    {
        "label": "\\gamma",
        "insertText": "\\gamma",
        "detail": "Chèn ký hiệu Gamma",
        "type": "snippet"
    },
    {
        "label": "\\Gamma",
        "insertText": "\\Gamma",
        "detail": "Chèn ký hiệu Gamma hoa",
        "type": "snippet"
    },
    {
        "label": "\\delta",
        "insertText": "\\delta",
        "detail": "Chèn ký hiệu Delta",
        "type": "snippet"
    },
    {
        "label": "\\Delta",
        "insertText": "\\Delta",
        "detail": "Chèn ký hiệu Delta hoa",
        "type": "snippet"
    },
    {
        "label": "\\epsilon",
        "insertText": "\\epsilon",
        "detail": "Chèn ký hiệu Epsilon",
        "type": "snippet"
    },
    {
        "label": "\\Epsilon",
        "insertText": "\\Epsilon",
        "detail": "Chèn ký hiệu Epsilon hoa",
        "type": "snippet"
    },
    {
        "label": "\\zeta",
        "insertText": "\\zeta",
        "detail": "Chèn ký hiệu Zeta",
        "type": "snippet"
    },
    {
        "label": "\\Zeta",
        "insertText": "\\Zeta",
        "detail": "Chèn ký hiệu Zeta hoa",
        "type": "snippet"
    },
    {
        "label": "\\eta",
        "insertText": "\\eta",
        "detail": "Chèn ký hiệu Eta",
        "type": "snippet"
    },
    {
        "label": "\\Eta",
        "insertText": "\\Eta",
        "detail": "Chèn ký hiệu Eta hoa",
        "type": "snippet"
    },
    {
        "label": "\\theta",
        "insertText": "\\theta",
        "detail": "Chèn ký hiệu Theta",
        "type": "snippet"
    },
    {
        "label": "\\Theta",
        "insertText": "\\Theta",
        "detail": "Chèn ký hiệu Theta hoa",
        "type": "snippet"
    },
    {
        "label": "\\iota",
        "insertText": "\\iota",
        "detail": "Chèn ký hiệu Iota",
        "type": "snippet"
    },
    {
        "label": "\\Iota",
        "insertText": "\\Iota",
        "detail": "Chèn ký hiệu Iota hoa",
        "type": "snippet"
    },
    {
        "label": "\\kappa",
        "insertText": "\\kappa",
        "detail": "Chèn ký hiệu Kappa",
        "type": "snippet"
    },
    {
        "label": "\\Kappa",
        "insertText": "\\Kappa",
        "detail": "Chèn ký hiệu Kappa hoa",
        "type": "snippet"
    },
    {
        "label": "\\lambda",
        "insertText": "\\lambda",
        "detail": "Chèn ký hiệu Lambda",
        "type": "snippet"
    },
    {
        "label": "\\Lambda",
        "insertText": "\\Lambda",
        "detail": "Chèn ký hiệu Lambda hoa",
        "type": "snippet"
    },
    {
        "label": "\\mu",
        "insertText": "\\mu",
        "detail": "Chèn ký hiệu Mu",
        "type": "snippet"
    },
    {
        "label": "\\Mu",
        "insertText": "\\Mu",
        "detail": "Chèn ký hiệu Mu hoa",
        "type": "snippet"
    },
    {
        "label": "\\nu",
        "insertText": "\\nu",
        "detail": "Chèn ký hiệu Nu",
        "type": "snippet"
    },
    {
        "label": "\\Nu",
        "insertText": "\\Nu",
        "detail": "Chèn ký hiệu Nu hoa",
        "type": "snippet"
    },
    {
        "label": "\\xi",
        "insertText": "\\xi",
        "detail": "Chèn ký hiệu Xi",
        "type": "snippet"
    },
    {
        "label": "\\Xi",
        "insertText": "\\Xi",
        "detail": "Chèn ký hiệu Xi hoa",
        "type": "snippet"
    },
    {
        "label": "\\pi",
        "insertText": "\\pi",
        "detail": "Chèn ký hiệu Pi",
        "type": "snippet"
    },
    {
        "label": "\\Pi",
        "insertText": "\\Pi",
        "detail": "Chèn ký hiệu Pi hoa",
        "type": "snippet"
    },
    {
        "label": "\\rho",
        "insertText": "\\rho",
        "detail": "Chèn ký hiệu Rho",
        "type": "snippet"
    },
    {
        "label": "\\Rho",
        "insertText": "\\Rho",
        "detail": "Chèn ký hiệu Rho hoa",
        "type": "snippet"
    },
    {
        "label": "\\sigma",
        "insertText": "\\sigma",
        "detail": "Chèn ký hiệu Sigma",
        "type": "snippet"
    },
    {
        "label": "\\Sigma",
        "insertText": "\\Sigma",
        "detail": "Chèn ký hiệu Sigma hoa",
        "type": "snippet"
    },
    {
        "label": "\\tau",
        "insertText": "\\tau",
        "detail": "Chèn ký hiệu Tau",
        "type": "snippet"
    },
    {
        "label": "\\Tau",
        "insertText": "\\Tau",
        "detail": "Chèn ký hiệu Tau hoa",
        "type": "snippet"
    },
    {
        "label": "\\phi",
        "insertText": "\\phi",
        "detail": "Chèn ký hiệu Phi",
        "type": "snippet"
    },
    {
        "label": "\\Phi",
        "insertText": "\\Phi",
        "detail": "Chèn ký hiệu Phi hoa",
        "type": "snippet"
    },
    {
        "label": "\\chi",
        "insertText": "\\chi",
        "detail": "Chèn ký hiệu Chi",
        "type": "snippet"
    },
    {
        "label": "\\Chi",
        "insertText": "\\Chi",
        "detail": "Chèn ký hiệu Chi hoa",
        "type": "snippet"
    },
    {
        "label": "\\psi",
        "insertText": "\\psi",
        "detail": "Chèn ký hiệu Psi",
        "type": "snippet"
    },
    {
        "label": "\\Psi",
        "insertText": "\\Psi",
        "detail": "Chèn ký hiệu Psi hoa",
        "type": "snippet"
    },
    {
        "label": "\\omega",
        "insertText": "\\omega",
        "detail": "Chèn ký hiệu Omega",
        "type": "snippet"
    },
    {
        "label": "\\Omega",
        "insertText": "\\Omega",
        "detail": "Chèn ký hiệu Omega hoa",
        "type": "snippet"
    },
]

LATEX_ENVIRONMENTS = [
    {
        "label": "document",
        "insertText": "\\begin{document}\n  ${1:content}\n\\end{document}",
        "detail": "Môi trường nội dung chính tài liệu",
        "type": "snippet"
    },
    {
        "label": "itemize",
        "insertText": "\\begin{itemize}\n  \\item ${1:item}\n\\end{itemize}",
        "detail": "Tạo danh sách ký hiệu đầu dòng",
        "type": "snippet"
    },
    {
        "label": "enumerate",
        "insertText": "\\begin{enumerate}\n  \\item ${1:item}\n\\end{enumerate}",
        "detail": "Tạo danh sách đánh số thứ tự",
        "type": "snippet"
    },
    {
        "label": "description",
        "insertText": "\\begin{description}\n  \\item[${1:label}] ${2:content}\n\\end{description}",
        "detail": "Tạo danh sách mô tả thuật ngữ",
        "type": "snippet"
    },
    {
        "label": "equation",
        "insertText": "\\begin{equation}\n  ${1:equation}\n\\end{equation}",
        "detail": "Tạo phương trình có đánh số",
        "type": "snippet"
    },
    {
        "label": "align",
        "insertText": "\\begin{align}\n  ${1:equation}\n\\end{align}",
        "detail": "Căn lề hệ phương trình",
        "type": "snippet"
    },
    {
        "label": "figure",
        "insertText": "\\begin{figure}[H]\n  \\centering\n  \\includegraphics[width=0.8\\textwidth]{${1:image}}\n  \\caption{${2:caption}}\n  \\label{fig:${3:label}}\n\\end{figure}",
        "detail": "Chèn hình ảnh có tiêu đề và nhãn",
        "type": "snippet"
    },
    {
        "label": "table",
        "insertText": "\\begin{table}[H]\n  \\centering\n  \\caption{${1:caption}}\n  \\label{tab:${2:label}}\n  \\begin{tabular}{${3:spec}}\n    ${4:content}\n  \\end{tabular}\n\\end{table}",
        "detail": "Chèn bảng biểu có tiêu đề và nhãn",
        "type": "snippet"
    },
    {
        "label": "tikzpicture",
        "insertText": "\\begin{tikzpicture}\n  ${1:draw_commands}\n\\end{tikzpicture}",
        "detail": "Môi trường vẽ hình đồ họa TikZ",
        "type": "snippet"
    },
    {
        "label": "center",
        "insertText": "\\begin{center}\n  ${1:content}\n\\end{center}",
        "detail": "Căn giữa khối nội dung",
        "type": "snippet"
    },
    {
        "label": "abstract",
        "insertText": "\\begin{abstract}\n  ${1:summary}\n\\end{abstract}",
        "detail": "Tạo phần tóm tắt nội dung",
        "type": "snippet"
    },
]
