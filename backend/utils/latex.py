from typing import Any
from core.response import APIResponse
LATEX_COMMANDS = [
    {
        "label": "\\usepackage[options]{package}",
        "insertText": "\\usepackage[${1:options}]{${2:package}}",
        "detail": "Khai báo gói",
        "type": "snippet"
    },
    {
        "label": "\\usepackage{package}",
        "insertText": "\\usepackage{${1:package}}",
        "detail": "Khai báo gói đơn giản",
        "type": "snippet"
    },
    {
        "label": "\\begin{environment}",
        "insertText": "\\begin{${1:environment}}\n\t$0\n\\end{${1:environment}}",
        "detail": "Bắt đầu khối",
        "type": "snippet"
    },
    {
        "label": "\\end{environment}",
        "insertText": "\\end{${1:environment}}",
        "detail": "Kết thúc khối",
        "type": "snippet"
    },
    {
        "label": "\\documentclass[options]{class}",
        "insertText": "\\documentclass[${1:options}]{${2:class}}",
        "detail": "Khai báo loại tài liệu",
        "type": "snippet"
    },
    {
        "label": "\\title{title}",
        "insertText": "\\title{${1:title}}",
        "detail": "Tiêu đề tài liệu",
        "type": "snippet"
    },
    {
        "label": "\\maketitle",
        "insertText": "\\maketitle",
        "detail": "Tạo tiêu đề",
        "type": "snippet"
    },
    {
        "label": "\\author{author}",
        "insertText": "\\author{${1:author}}",
        "detail": "Tên tác giả",
        "type": "snippet"
    },
    {
        "label": "\\thanks{arg1}",
        "insertText": "\\thanks{${1:arg1}}",
        "detail": "Lời cảm ơn",
        "type": "snippet"
    },
    {
        "label": "\\date{date}",
        "insertText": "\\date{${1:date}}",
        "detail": "Ngày tháng",
        "type": "snippet"
    },
    {
        "label": "\\today",
        "insertText": "\\today",
        "detail": "Ngày hôm nay",
        "type": "snippet"
    },
    {
        "label": "\\tableofcontents",
        "insertText": "\\tableofcontents",
        "detail": "Mục lục",
        "type": "snippet"
    },
    {
        "label": "\\addcontentsline{ext}{unit}{text}",
        "insertText": "\\addcontentsline{${1:ext}}{${2:unit}}{${3:text}}",
        "detail": "Thêm dòng mục lục",
        "type": "snippet"
    },
    {
        "label": "\\part{title}",
        "insertText": "\\part{${1:title}}",
        "detail": "Phần lớn",
        "type": "snippet"
    },
    {
        "label": "\\chapter{title}",
        "insertText": "\\chapter{${1:title}}",
        "detail": "Chương",
        "type": "snippet"
    },
    {
        "label": "\\section{title}",
        "insertText": "\\section{${1:title}}",
        "detail": "Mục lớn",
        "type": "snippet"
    },
    {
        "label": "\\subsection{title}",
        "insertText": "\\subsection{${1:title}}",
        "detail": "Mục con",
        "type": "snippet"
    },
    {
        "label": "\\subsubsection{title}",
        "insertText": "\\subsubsection{${1:title}}",
        "detail": "Mục nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\paragraph{title}",
        "insertText": "\\paragraph{${1:title}}",
        "detail": "Đoạn văn",
        "type": "snippet"
    },
    {
        "label": "\\subparagraph{title}",
        "insertText": "\\subparagraph{${1:title}}",
        "detail": "Đoạn phụ",
        "type": "snippet"
    },
    {
        "label": "\\textbf{text}",
        "insertText": "\\textbf{${1:text}}",
        "detail": "In đậm",
        "type": "snippet"
    },
    {
        "label": "\\textit{text}",
        "insertText": "\\textit{${1:text}}",
        "detail": "In nghiêng",
        "type": "snippet"
    },
    {
        "label": "\\underline{text}",
        "insertText": "\\underline{${1:text}}",
        "detail": "Gạch chân",
        "type": "snippet"
    },
    {
        "label": "\\emph{text}",
        "insertText": "\\emph{${1:text}}",
        "detail": "Nhấn mạnh",
        "type": "snippet"
    },
    {
        "label": "\\verb||",
        "insertText": "\\verb||",
        "detail": "Khối code",
        "type": "snippet"
    },
    {
        "label": "\\copyright",
        "insertText": "\\copyright",
        "detail": "Ký hiệu bản quyền",
        "type": "snippet"
    },
    {
        "label": "\\textregistered",
        "insertText": "\\textregistered",
        "detail": "Nhãn hiệu đã đăng ký",
        "type": "snippet"
    },
    {
        "label": "\\texttrademark",
        "insertText": "\\texttrademark",
        "detail": "Nhãn hiệu thương mại",
        "type": "snippet"
    },
    {
        "label": "\\pounds",
        "insertText": "\\pounds",
        "detail": "Đơn vị Bảng Anh",
        "type": "snippet"
    },
    {
        "label": "\\euro",
        "insertText": "\\euro",
        "detail": "Đơn vị Euro",
        "type": "snippet"
    },
    {
        "label": "\\item",
        "insertText": "\\item $0",
        "detail": "Mục danh sách",
        "type": "snippet"
    },
    {
        "label": "\\setlist[options]arg2",
        "insertText": "\\setlist[${1:options}]${2:arg2}",
        "detail": "Cấu hình danh sách toàn cục",
        "type": "snippet"
    },
    {
        "label": "\\setlist{nosep}",
        "insertText": "\\setlist{nosep}",
        "detail": "Loại bỏ khoảng cách danh sách",
        "type": "snippet"
    },
    {
        "label": "\\arabic{arg1}",
        "insertText": "\\arabic{${1:arg1}}",
        "detail": "Số Ả Rập",
        "type": "snippet"
    },
    {
        "label": "\\roman{arg1}",
        "insertText": "\\roman{${1:arg1}}",
        "detail": "Số La Mã thường",
        "type": "snippet"
    },
    {
        "label": "\\Roman{arg1}",
        "insertText": "\\Roman{${1:arg1}}",
        "detail": "Số La Mã hoa",
        "type": "snippet"
    },
    {
        "label": "\\alph{arg1}",
        "insertText": "\\alph{${1:arg1}}",
        "detail": "Chữ cái thường",
        "type": "snippet"
    },
    {
        "label": "\\Alph{arg1}",
        "insertText": "\\Alph{${1:arg1}}",
        "detail": "Chữ cái hoa",
        "type": "snippet"
    },
    {
        "label": "\\(...\\)",
        "insertText": "\\(...\\)",
        "detail": "Toán trong dòng ngoặc tròn",
        "type": "snippet"
    },
    {
        "label": "\\[...\\]",
        "insertText": "\\[...\\]",
        "detail": "Toán riêng dòng ngoặc vuông",
        "type": "snippet"
    },
    {
        "label": "\\frac{numerator}{denominator}",
        "insertText": "\\frac{${1:numerator}}{${2:denominator}}",
        "detail": "Phân số",
        "type": "snippet"
    },
    {
        "label": "\\dfrac{numerator}{denominator}",
        "insertText": "\\dfrac{${1:numerator}}{${2:denominator}}",
        "detail": "Phân số hiển thị lớn",
        "type": "snippet"
    },
    {
        "label": "\\tfrac{numerator}{denominator}",
        "insertText": "\\tfrac{${1:numerator}}{${2:denominator}}",
        "detail": "Phân số trong dòng",
        "type": "snippet"
    },
    {
        "label": "\\cfrac{numerator}{denominator}",
        "insertText": "\\cfrac{${1:numerator}}{${2:denominator}}",
        "detail": "Liên phân số",
        "type": "snippet"
    },
    {
        "label": "\\genfrac{arg1}{arg2}arg3arg4arg5arg6",
        "insertText": "\\genfrac{${1:arg1}}{${2:arg2}}${3:arg3}{${4:arg4}}${5:arg5}{${6:arg6}}",
        "detail": "Phân số tổng quát",
        "type": "snippet"
    },
    {
        "label": "\\binom{n}{k}",
        "insertText": "\\binom{${1:n}}{${2:k}}",
        "detail": "Tổ hợp chập",
        "type": "snippet"
    },
    {
        "label": "\\sqrt[n]{radicand}",
        "insertText": "\\sqrt[${1:n}]{${2:radicand}}",
        "detail": "Căn bậc hai",
        "type": "snippet"
    },
    {
        "label": "\\text{text}",
        "insertText": "\\text{${1:text}}",
        "detail": "Văn bản trong công thức",
        "type": "snippet"
    },
    {
        "label": "\\left ... \\right",
        "insertText": "\\left ... \\right",
        "detail": "Ngoặc tự động điều chỉnh",
        "type": "snippet"
    },
    {
        "label": "\\left. ... \\right.",
        "insertText": "\\left. ... \\right.",
        "detail": "Ngoặc ảo",
        "type": "snippet"
    },
    {
        "label": "\\{ ... \\}",
        "insertText": "\\{ ... \\}",
        "detail": "Ngoặc nhọn",
        "type": "snippet"
    },
    {
        "label": "\\langle ... \\rangle",
        "insertText": "\\langle ... \\rangle",
        "detail": "Ngoặc góc",
        "type": "snippet"
    },
    {
        "label": "\\| ... \\|",
        "insertText": "\\| ... \\|",
        "detail": "Dấu chuẩn",
        "type": "snippet"
    },
    {
        "label": "\\lfloor ... \\rfloor",
        "insertText": "\\lfloor ... \\rfloor",
        "detail": "Hàm sàn",
        "type": "snippet"
    },
    {
        "label": "\\lceil ... \\rceil",
        "insertText": "\\lceil ... \\rceil",
        "detail": "Hàm trần",
        "type": "snippet"
    },
    {
        "label": "\\big",
        "insertText": "\\big",
        "detail": "Kích thước lớn",
        "type": "snippet"
    },
    {
        "label": "\\Big",
        "insertText": "\\Big",
        "detail": "Kích thước lớn hơn",
        "type": "snippet"
    },
    {
        "label": "\\bigg",
        "insertText": "\\bigg",
        "detail": "Kích thước rất lớn",
        "type": "snippet"
    },
    {
        "label": "\\Bigg",
        "insertText": "\\Bigg",
        "detail": "Kích thước lớn nhất",
        "type": "snippet"
    },
    {
        "label": "\\cancel{arg1}",
        "insertText": "\\cancel{${1:arg1}}",
        "detail": "Dấu gạch chéo xóa",
        "type": "snippet"
    },
    {
        "label": "\\bcancel{arg1}",
        "insertText": "\\bcancel{${1:arg1}}",
        "detail": "Dấu gạch ngược xóa",
        "type": "snippet"
    },
    {
        "label": "\\xcancel{arg1}",
        "insertText": "\\xcancel{${1:arg1}}",
        "detail": "Dấu gạch chéo X xóa",
        "type": "snippet"
    },
    {
        "label": "\\cancelto{arg1}{arg2}",
        "insertText": "\\cancelto{${1:arg1}}{${2:arg2}}",
        "detail": "Xóa tiến tới giá trị",
        "type": "snippet"
    },
    {
        "label": "\\int_{lower}^{upper}",
        "insertText": "\\int_{${1:lower}}^{${2:upper}}",
        "detail": "Tích phân",
        "type": "snippet"
    },
    {
        "label": "\\oint",
        "insertText": "\\oint",
        "detail": "Tích phân đường kín",
        "type": "snippet"
    },
    {
        "label": "\\iint",
        "insertText": "\\iint",
        "detail": "Tích phân hai lớp",
        "type": "snippet"
    },
    {
        "label": "\\iiint",
        "insertText": "\\iiint",
        "detail": "Tích phân ba lớp",
        "type": "snippet"
    },
    {
        "label": "\\iiiint",
        "insertText": "\\iiiint",
        "detail": "Tích phân bốn lớp",
        "type": "snippet"
    },
    {
        "label": "\\idotsint",
        "insertText": "\\idotsint",
        "detail": "Tích phân n lớp",
        "type": "snippet"
    },
    {
        "label": "\\sum_{lower}^{upper}",
        "insertText": "\\sum_{${1:lower}}^{${2:upper}}",
        "detail": "Tổng chuỗi",
        "type": "snippet"
    },
    {
        "label": "\\prod_{lower}^{upper}",
        "insertText": "\\prod_{${1:lower}}^{${2:upper}}",
        "detail": "Tích chuỗi",
        "type": "snippet"
    },
    {
        "label": "\\coprod",
        "insertText": "\\coprod",
        "detail": "Đồng tích",
        "type": "snippet"
    },
    {
        "label": "\\lim_{x \\to a}",
        "insertText": "\\lim_{${1:x} \\to ${2:a}}",
        "detail": "Giới hạn",
        "type": "snippet"
    },
    {
        "label": "\\limits_{lower}^{upper}",
        "insertText": "\\limits_{${1:lower}}^{${2:upper}}",
        "detail": "Vị trí cận",
        "type": "snippet"
    },
    {
        "label": "\\sin",
        "insertText": "\\sin",
        "detail": "Hàm Sin",
        "type": "snippet"
    },
    {
        "label": "\\cos",
        "insertText": "\\cos",
        "detail": "Hàm Cos",
        "type": "snippet"
    },
    {
        "label": "\\tan",
        "insertText": "\\tan",
        "detail": "Hàm Tan",
        "type": "snippet"
    },
    {
        "label": "\\csc",
        "insertText": "\\csc",
        "detail": "Hàm Cosecant",
        "type": "snippet"
    },
    {
        "label": "\\sec",
        "insertText": "\\sec",
        "detail": "Hàm Secant",
        "type": "snippet"
    },
    {
        "label": "\\cot",
        "insertText": "\\cot",
        "detail": "Hàm Cotangent",
        "type": "snippet"
    },
    {
        "label": "\\arcsin",
        "insertText": "\\arcsin",
        "detail": "Hàm Arcsin",
        "type": "snippet"
    },
    {
        "label": "\\arccos",
        "insertText": "\\arccos",
        "detail": "Hàm Arccos",
        "type": "snippet"
    },
    {
        "label": "\\arctan",
        "insertText": "\\arctan",
        "detail": "Hàm Arctan",
        "type": "snippet"
    },
    {
        "label": "\\sinh",
        "insertText": "\\sinh",
        "detail": "Hàm Sin Hyperbolic",
        "type": "snippet"
    },
    {
        "label": "\\cosh",
        "insertText": "\\cosh",
        "detail": "Hàm Cos Hyperbolic",
        "type": "snippet"
    },
    {
        "label": "\\tanh",
        "insertText": "\\tanh",
        "detail": "Hàm Tan Hyperbolic",
        "type": "snippet"
    },
    {
        "label": "\\coth",
        "insertText": "\\coth",
        "detail": "Hàm Cot Hyperbolic",
        "type": "snippet"
    },
    {
        "label": "\\log",
        "insertText": "\\log",
        "detail": "Logarit cơ số 10",
        "type": "snippet"
    },
    {
        "label": "\\ln",
        "insertText": "\\ln",
        "detail": "Logarit tự nhiên",
        "type": "snippet"
    },
    {
        "label": "\\lg",
        "insertText": "\\lg",
        "detail": "Logarit cơ số 2",
        "type": "snippet"
    },
    {
        "label": "\\exp",
        "insertText": "\\exp",
        "detail": "Hàm mũ",
        "type": "snippet"
    },
    {
        "label": "\\min",
        "insertText": "\\min",
        "detail": "Giá trị nhỏ nhất",
        "type": "snippet"
    },
    {
        "label": "\\max",
        "insertText": "\\max",
        "detail": "Giá trị lớn nhất",
        "type": "snippet"
    },
    {
        "label": "\\sup",
        "insertText": "\\sup",
        "detail": "Cận trên đúng",
        "type": "snippet"
    },
    {
        "label": "\\inf",
        "insertText": "\\inf",
        "detail": "Cận dưới đúng",
        "type": "snippet"
    },
    {
        "label": "\\liminf",
        "insertText": "\\liminf",
        "detail": "Giới hạn dưới",
        "type": "snippet"
    },
    {
        "label": "\\limsup",
        "insertText": "\\limsup",
        "detail": "Giới hạn trên",
        "type": "snippet"
    },
    {
        "label": "\\arg",
        "insertText": "\\arg",
        "detail": "Số phức Argument",
        "type": "snippet"
    },
    {
        "label": "\\deg",
        "insertText": "\\deg",
        "detail": "Độ",
        "type": "snippet"
    },
    {
        "label": "\\det",
        "insertText": "\\det",
        "detail": "Định thức",
        "type": "snippet"
    },
    {
        "label": "\\dim",
        "insertText": "\\dim",
        "detail": "Số chiều",
        "type": "snippet"
    },
    {
        "label": "\\gcd",
        "insertText": "\\gcd",
        "detail": "Ước chung lớn nhất",
        "type": "snippet"
    },
    {
        "label": "\\lcm",
        "insertText": "\\lcm",
        "detail": "Bội chung nhỏ nhất",
        "type": "snippet"
    },
    {
        "label": "\\hom",
        "insertText": "\\hom",
        "detail": "Đồng cấu",
        "type": "snippet"
    },
    {
        "label": "\\ker",
        "insertText": "\\ker",
        "detail": "Hạt nhân",
        "type": "snippet"
    },
    {
        "label": "\\Pr",
        "insertText": "\\Pr",
        "detail": "Xác suất",
        "type": "snippet"
    },
    {
        "label": "\\DeclareMathOperator",
        "insertText": "\\DeclareMathOperator",
        "detail": "Khai báo toán tử",
        "type": "snippet"
    },
    {
        "label": "\\DeclareMathOperator*",
        "insertText": "\\DeclareMathOperator*",
        "detail": "Khai báo toán tử sao",
        "type": "snippet"
    },
    {
        "label": "\\prescript{arg1}{arg2}arg3",
        "insertText": "\\prescript{${1:arg1}}{${2:arg2}}${3:arg3}",
        "detail": "Chỉ số trên trái",
        "type": "snippet"
    },
    {
        "label": "\\DeclarePairedDelimiter{\\cmd}{left}{right}",
        "insertText": "\\DeclarePairedDelimiter{\\cmd}{left}{right}",
        "detail": "Dấu ngoặc ghép đôi",
        "type": "snippet"
    },
    {
        "label": "\\underbracket{arg1}",
        "insertText": "\\underbracket{${1:arg1}}",
        "detail": "Dấu ngoặc vuông dưới",
        "type": "snippet"
    },
    {
        "label": "\\overbracket{arg1}",
        "insertText": "\\overbracket{${1:arg1}}",
        "detail": "Dấu ngoặc vuông trên",
        "type": "snippet"
    },
    {
        "label": "\\xleftrightarrow{arg1}",
        "insertText": "\\xleftrightarrow{${1:arg1}}",
        "detail": "Mũi tên hai chiều co giãn",
        "type": "snippet"
    },
    {
        "label": "\\xLeftrightarrow{arg1}",
        "insertText": "\\xLeftrightarrow{${1:arg1}}",
        "detail": "Mũi tên tương đương co giãn",
        "type": "snippet"
    },
    {
        "label": "\\overline{arg1}",
        "insertText": "\\overline{${1:arg1}}",
        "detail": "Liên kết dòng trên",
        "type": "snippet"
    },
    {
        "label": "\\underbar{arg1}",
        "insertText": "\\underbar{${1:arg1}}",
        "detail": "Gạch ngang dưới",
        "type": "snippet"
    },
    {
        "label": "\\dashv",
        "insertText": "\\dashv",
        "detail": "Phần tử lùi dần",
        "type": "snippet"
    },
    {
        "label": "\\vdash",
        "insertText": "\\vdash",
        "detail": "Phần tử tiến dần",
        "type": "snippet"
    },
    {
        "label": "\\;",
        "insertText": "\\;",
        "detail": "Dấu chấm phẩy toán học",
        "type": "snippet"
    },
    {
        "label": "\\!",
        "insertText": "\\!",
        "detail": "Khoảng cách rất nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\intertext{arg1}",
        "insertText": "\\intertext{${1:arg1}}",
        "detail": "Văn bản giữa công thức",
        "type": "snippet"
    },
    {
        "label": "\\shortintertext{arg1}",
        "insertText": "\\shortintertext{${1:arg1}}",
        "detail": "Văn bản ngắn giữa công thức",
        "type": "snippet"
    },
    {
        "label": "\\substack{arg1}",
        "insertText": "\\substack{${1:arg1}}",
        "detail": "Chèn biểu thức nhiều dòng",
        "type": "snippet"
    },
    {
        "label": "\\MoveEqLeft",
        "insertText": "\\MoveEqLeft",
        "detail": "Căn lề trái phương trình",
        "type": "snippet"
    },
    {
        "label": "\\coloneqq",
        "insertText": "\\coloneqq",
        "detail": "Dấu bằng định nghĩa",
        "type": "snippet"
    },
    {
        "label": "\\xlongleftrightarrow{arg1}",
        "insertText": "\\xlongleftrightarrow{${1:arg1}}",
        "detail": "Mũi tên dài hai chiều co giãn",
        "type": "snippet"
    },
    {
        "label": "\\makebox[width]arg1",
        "insertText": "\\makebox[width]${1:arg1}",
        "detail": "Xử lý chiều rộng ma trận",
        "type": "snippet"
    },
    {
        "label": "\\alpha",
        "insertText": "\\alpha",
        "detail": "Ký tự Alpha",
        "type": "snippet"
    },
    {
        "label": "\\beta",
        "insertText": "\\beta",
        "detail": "Ký tự Beta",
        "type": "snippet"
    },
    {
        "label": "\\gamma",
        "insertText": "\\gamma",
        "detail": "Ký tự Gamma",
        "type": "snippet"
    },
    {
        "label": "\\delta",
        "insertText": "\\delta",
        "detail": "Ký tự Delta",
        "type": "snippet"
    },
    {
        "label": "\\epsilon",
        "insertText": "\\epsilon",
        "detail": "Ký tự Epsilon",
        "type": "snippet"
    },
    {
        "label": "\\varepsilon",
        "insertText": "\\varepsilon",
        "detail": "Ký tự Epsilon biến thể",
        "type": "snippet"
    },
    {
        "label": "\\zeta",
        "insertText": "\\zeta",
        "detail": "Ký tự Zeta",
        "type": "snippet"
    },
    {
        "label": "\\eta",
        "insertText": "\\eta",
        "detail": "Ký tự Eta",
        "type": "snippet"
    },
    {
        "label": "\\theta",
        "insertText": "\\theta",
        "detail": "Ký tự Theta",
        "type": "snippet"
    },
    {
        "label": "\\vartheta",
        "insertText": "\\vartheta",
        "detail": "Ký tự Theta biến thể",
        "type": "snippet"
    },
    {
        "label": "\\iota",
        "insertText": "\\iota",
        "detail": "Ký tự Iota",
        "type": "snippet"
    },
    {
        "label": "\\kappa",
        "insertText": "\\kappa",
        "detail": "Ký tự Kappa",
        "type": "snippet"
    },
    {
        "label": "\\lambda",
        "insertText": "\\lambda",
        "detail": "Ký tự Lambda",
        "type": "snippet"
    },
    {
        "label": "\\mu",
        "insertText": "\\mu",
        "detail": "Ký tự Mu",
        "type": "snippet"
    },
    {
        "label": "\\nu",
        "insertText": "\\nu",
        "detail": "Ký tự Nu",
        "type": "snippet"
    },
    {
        "label": "\\xi",
        "insertText": "\\xi",
        "detail": "Ký tự Xi",
        "type": "snippet"
    },
    {
        "label": "\\pi",
        "insertText": "\\pi",
        "detail": "Ký tự Pi",
        "type": "snippet"
    },
    {
        "label": "\\rho",
        "insertText": "\\rho",
        "detail": "Ký tự Rho",
        "type": "snippet"
    },
    {
        "label": "\\varrho",
        "insertText": "\\varrho",
        "detail": "Ký tự Rho biến thể",
        "type": "snippet"
    },
    {
        "label": "\\sigma",
        "insertText": "\\sigma",
        "detail": "Ký tự Sigma",
        "type": "snippet"
    },
    {
        "label": "\\tau",
        "insertText": "\\tau",
        "detail": "Ký tự Tau",
        "type": "snippet"
    },
    {
        "label": "\\upsilon",
        "insertText": "\\upsilon",
        "detail": "Ký tự Upsilon",
        "type": "snippet"
    },
    {
        "label": "\\phi",
        "insertText": "\\phi",
        "detail": "Ký tự Phi",
        "type": "snippet"
    },
    {
        "label": "\\varphi",
        "insertText": "\\varphi",
        "detail": "Ký tự Phi biến thể",
        "type": "snippet"
    },
    {
        "label": "\\chi",
        "insertText": "\\chi",
        "detail": "Ký tự Chi",
        "type": "snippet"
    },
    {
        "label": "\\psi",
        "insertText": "\\psi",
        "detail": "Ký tự Psi",
        "type": "snippet"
    },
    {
        "label": "\\omega",
        "insertText": "\\omega",
        "detail": "Ký tự Omega",
        "type": "snippet"
    },
    {
        "label": "\\Gamma",
        "insertText": "\\Gamma",
        "detail": "Ký tự Gamma hoa",
        "type": "snippet"
    },
    {
        "label": "\\Delta",
        "insertText": "\\Delta",
        "detail": "Ký tự Delta hoa",
        "type": "snippet"
    },
    {
        "label": "\\Theta",
        "insertText": "\\Theta",
        "detail": "Ký tự Theta hoa",
        "type": "snippet"
    },
    {
        "label": "\\Lambda",
        "insertText": "\\Lambda",
        "detail": "Ký tự Lambda hoa",
        "type": "snippet"
    },
    {
        "label": "\\Xi",
        "insertText": "\\Xi",
        "detail": "Ký tự Xi hoa",
        "type": "snippet"
    },
    {
        "label": "\\Pi",
        "insertText": "\\Pi",
        "detail": "Ký tự Pi hoa",
        "type": "snippet"
    },
    {
        "label": "\\Sigma",
        "insertText": "\\Sigma",
        "detail": "Ký tự Sigma hoa",
        "type": "snippet"
    },
    {
        "label": "\\Upsilon",
        "insertText": "\\Upsilon",
        "detail": "Ký tự Upsilon hoa",
        "type": "snippet"
    },
    {
        "label": "\\Phi",
        "insertText": "\\Phi",
        "detail": "Ký tự Phi hoa",
        "type": "snippet"
    },
    {
        "label": "\\Psi",
        "insertText": "\\Psi",
        "detail": "Ký tự Psi hoa",
        "type": "snippet"
    },
    {
        "label": "\\Omega",
        "insertText": "\\Omega",
        "detail": "Ký tự Omega hoa",
        "type": "snippet"
    },
    {
        "label": "\\leftarrow",
        "insertText": "\\leftarrow",
        "detail": "Mũi tên sang trái",
        "type": "snippet"
    },
    {
        "label": "\\Leftarrow",
        "insertText": "\\Leftarrow",
        "detail": "Mũi tên sang trái kép",
        "type": "snippet"
    },
    {
        "label": "\\rightarrow",
        "insertText": "\\rightarrow",
        "detail": "Mũi tên sang phải",
        "type": "snippet"
    },
    {
        "label": "\\Rightarrow",
        "insertText": "\\Rightarrow",
        "detail": "Mũi tên sang phải kép",
        "type": "snippet"
    },
    {
        "label": "\\implies",
        "insertText": "\\implies",
        "detail": "Mũi tên suy ra",
        "type": "snippet"
    },
    {
        "label": "\\iff",
        "insertText": "\\iff",
        "detail": "Mũi tên tương đương",
        "type": "snippet"
    },
    {
        "label": "\\leftrightarrow",
        "insertText": "\\leftrightarrow",
        "detail": "Mũi tên hai chiều",
        "type": "snippet"
    },
    {
        "label": "\\Leftrightarrow",
        "insertText": "\\Leftrightarrow",
        "detail": "Mũi tên tương đương hẹp",
        "type": "snippet"
    },
    {
        "label": "\\uparrow",
        "insertText": "\\uparrow",
        "detail": "Mũi tên hướng lên",
        "type": "snippet"
    },
    {
        "label": "\\Uparrow",
        "insertText": "\\Uparrow",
        "detail": "Mũi tên hướng lên kép",
        "type": "snippet"
    },
    {
        "label": "\\downarrow",
        "insertText": "\\downarrow",
        "detail": "Mũi tên hướng xuống",
        "type": "snippet"
    },
    {
        "label": "\\Downarrow",
        "insertText": "\\Downarrow",
        "detail": "Mũi tên hướng xuống kép",
        "type": "snippet"
    },
    {
        "label": "\\Updownarrow",
        "insertText": "\\Updownarrow",
        "detail": "Mũi tên lên xuống",
        "type": "snippet"
    },
    {
        "label": "\\mapsto",
        "insertText": "\\mapsto",
        "detail": "Mũi tên ánh xạ tới",
        "type": "snippet"
    },
    {
        "label": "\\longmapsto",
        "insertText": "\\longmapsto",
        "detail": "Mũi tên ánh xạ dài",
        "type": "snippet"
    },
    {
        "label": "\\nearrow",
        "insertText": "\\nearrow",
        "detail": "Mũi tên hướng Đông Bắc",
        "type": "snippet"
    },
    {
        "label": "\\searrow",
        "insertText": "\\searrow",
        "detail": "Mũi tên hướng Đông Nam",
        "type": "snippet"
    },
    {
        "label": "\\swarrow",
        "insertText": "\\swarrow",
        "detail": "Mũi tên hướng Tây Nam",
        "type": "snippet"
    },
    {
        "label": "\\nwarrow",
        "insertText": "\\nwarrow",
        "detail": "Mũi tên hướng Tây Bắc",
        "type": "snippet"
    },
    {
        "label": "\\leftharpoonup",
        "insertText": "\\leftharpoonup",
        "detail": "Mũi tên móc lên trái",
        "type": "snippet"
    },
    {
        "label": "\\rightharpoonup",
        "insertText": "\\rightharpoonup",
        "detail": "Mũi tên móc lên phải",
        "type": "snippet"
    },
    {
        "label": "\\leftharpoondown",
        "insertText": "\\leftharpoondown",
        "detail": "Mũi tên móc xuống trái",
        "type": "snippet"
    },
    {
        "label": "\\rightharpoondown",
        "insertText": "\\rightharpoondown",
        "detail": "Mũi tên móc xuống phải",
        "type": "snippet"
    },
    {
        "label": "\\rightleftharpoons",
        "insertText": "\\rightleftharpoons",
        "detail": "Mũi tên cân bằng hóa học",
        "type": "snippet"
    },
    {
        "label": "\\to",
        "insertText": "\\to",
        "detail": "Mũi tên tiến tới",
        "type": "snippet"
    },
    {
        "label": "\\longleftarrow",
        "insertText": "\\longleftarrow",
        "detail": "Mũi tên dài sang trái",
        "type": "snippet"
    },
    {
        "label": "\\longrightarrow",
        "insertText": "\\longrightarrow",
        "detail": "Mũi tên dài sang phải",
        "type": "snippet"
    },
    {
        "label": "\\longleftrightarrow",
        "insertText": "\\longleftrightarrow",
        "detail": "Mũi tên dài hai chiều",
        "type": "snippet"
    },
    {
        "label": "\\Longleftarrow",
        "insertText": "\\Longleftarrow",
        "detail": "Mũi tên dài kép sang trái",
        "type": "snippet"
    },
    {
        "label": "\\Longrightarrow",
        "insertText": "\\Longrightarrow",
        "detail": "Mũi tên dài kép sang phải",
        "type": "snippet"
    },
    {
        "label": "\\Longleftrightarrow",
        "insertText": "\\Longleftrightarrow",
        "detail": "Mũi tên dài kép hai chiều",
        "type": "snippet"
    },
    {
        "label": "\\xrightarrow{arg1}",
        "insertText": "\\xrightarrow{${1:arg1}}",
        "detail": "Mũi tên phải co giãn",
        "type": "snippet"
    },
    {
        "label": "\\xleftarrow{arg1}",
        "insertText": "\\xleftarrow{${1:arg1}}",
        "detail": "Mũi tên trái co giãn",
        "type": "snippet"
    },
    {
        "label": "\\xRightarrow{arg1}",
        "insertText": "\\xRightarrow{${1:arg1}}",
        "detail": "Mũi tên phải kép co giãn",
        "type": "snippet"
    },
    {
        "label": "\\xLeftarrow{arg1}",
        "insertText": "\\xLeftarrow{${1:arg1}}",
        "detail": "Mũi tên trái kép co giãn",
        "type": "snippet"
    },
    {
        "label": "\\leadsto",
        "insertText": "\\leadsto",
        "detail": "Mũi tên ngoằn nghèo",
        "type": "snippet"
    },
    {
        "label": "\\leftrightharpoons",
        "insertText": "\\leftrightharpoons",
        "detail": "Mũi tên móc cân bằng trái",
        "type": "snippet"
    },
    {
        "label": "\\times",
        "insertText": "\\times",
        "detail": "Dấu nhân",
        "type": "snippet"
    },
    {
        "label": "\\cdot",
        "insertText": "\\cdot",
        "detail": "Dấu nhân chấm",
        "type": "snippet"
    },
    {
        "label": "\\div",
        "insertText": "\\div",
        "detail": "Dấu chia",
        "type": "snippet"
    },
    {
        "label": "\\pm",
        "insertText": "\\pm",
        "detail": "Cộng trừ",
        "type": "snippet"
    },
    {
        "label": "\\mp",
        "insertText": "\\mp",
        "detail": "Trừ cộng",
        "type": "snippet"
    },
    {
        "label": "\\ast",
        "insertText": "\\ast",
        "detail": "Dấu hoa thị",
        "type": "snippet"
    },
    {
        "label": "\\star",
        "insertText": "\\star",
        "detail": "Dấu sao",
        "type": "snippet"
    },
    {
        "label": "\\circ",
        "insertText": "\\circ",
        "detail": "Hợp thành",
        "type": "snippet"
    },
    {
        "label": "\\bullet",
        "insertText": "\\bullet",
        "detail": "Dấu chấm tròn",
        "type": "snippet"
    },
    {
        "label": "\\diamond",
        "insertText": "\\diamond",
        "detail": "Hình thoi",
        "type": "snippet"
    },
    {
        "label": "\\wedge",
        "insertText": "\\wedge",
        "detail": "Tích ngoài",
        "type": "snippet"
    },
    {
        "label": "\\vee",
        "insertText": "\\vee",
        "detail": "Hợp logic",
        "type": "snippet"
    },
    {
        "label": "\\neq",
        "insertText": "\\neq",
        "detail": "Dấu khác",
        "type": "snippet"
    },
    {
        "label": "\\leq",
        "insertText": "\\leq",
        "detail": "Nhỏ hơn hoặc bằng",
        "type": "snippet"
    },
    {
        "label": "\\geq",
        "insertText": "\\geq",
        "detail": "Lớn hơn hoặc bằng",
        "type": "snippet"
    },
    {
        "label": "\\in",
        "insertText": "\\in",
        "detail": "Thuộc tập hợp",
        "type": "snippet"
    },
    {
        "label": "\\notin",
        "insertText": "\\notin",
        "detail": "Không thuộc tập hợp",
        "type": "snippet"
    },
    {
        "label": "\\subset",
        "insertText": "\\subset",
        "detail": "Tập con",
        "type": "snippet"
    },
    {
        "label": "\\subseteq",
        "insertText": "\\subseteq",
        "detail": "Tập con hoặc bằng",
        "type": "snippet"
    },
    {
        "label": "\\subsetneq",
        "insertText": "\\subsetneq",
        "detail": "Tập con thực sự",
        "type": "snippet"
    },
    {
        "label": "\\supset",
        "insertText": "\\supset",
        "detail": "Chứa",
        "type": "snippet"
    },
    {
        "label": "\\supseteq",
        "insertText": "\\supseteq",
        "detail": "Chứa hoặc bằng",
        "type": "snippet"
    },
    {
        "label": "\\supsetneq",
        "insertText": "\\supsetneq",
        "detail": "Chứa thực sự",
        "type": "snippet"
    },
    {
        "label": "\\cup",
        "insertText": "\\cup",
        "detail": "Hợp tập hợp",
        "type": "snippet"
    },
    {
        "label": "\\cap",
        "insertText": "\\cap",
        "detail": "Giao tập hợp",
        "type": "snippet"
    },
    {
        "label": "\\setminus",
        "insertText": "\\setminus",
        "detail": "Hiệu tập hợp",
        "type": "snippet"
    },
    {
        "label": "\\bigcup",
        "insertText": "\\bigcup",
        "detail": "Hợp lớn",
        "type": "snippet"
    },
    {
        "label": "\\bigcap",
        "insertText": "\\bigcap",
        "detail": "Giao lớn",
        "type": "snippet"
    },
    {
        "label": "\\bigsqcup",
        "insertText": "\\bigsqcup",
        "detail": "Hợp không giao lớn",
        "type": "snippet"
    },
    {
        "label": "\\sqcup",
        "insertText": "\\sqcup",
        "detail": "Hợp không giao nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\sqcap",
        "insertText": "\\sqcap",
        "detail": "Giao hình vuông",
        "type": "snippet"
    },
    {
        "label": "\\uplus",
        "insertText": "\\uplus",
        "detail": "Hợp không giao",
        "type": "snippet"
    },
    {
        "label": "\\biguplus",
        "insertText": "\\biguplus",
        "detail": "Hợp không giao lớn",
        "type": "snippet"
    },
    {
        "label": "\\nsubset",
        "insertText": "\\nsubset",
        "detail": "Phủ định tập con",
        "type": "snippet"
    },
    {
        "label": "\\nsubseteq",
        "insertText": "\\nsubseteq",
        "detail": "Phủ định tập con bằng",
        "type": "snippet"
    },
    {
        "label": "\\ll",
        "insertText": "\\ll",
        "detail": "Nhỏ hơn nhiều",
        "type": "snippet"
    },
    {
        "label": "\\gg",
        "insertText": "\\gg",
        "detail": "Lớn hơn nhiều",
        "type": "snippet"
    },
    {
        "label": "\\sim",
        "insertText": "\\sim",
        "detail": "Tương đương",
        "type": "snippet"
    },
    {
        "label": "\\approx",
        "insertText": "\\approx",
        "detail": "Xấp xỉ bằng",
        "type": "snippet"
    },
    {
        "label": "\\simeq",
        "insertText": "\\simeq",
        "detail": "Xấp xỉ",
        "type": "snippet"
    },
    {
        "label": "\\equiv",
        "insertText": "\\equiv",
        "detail": "Đồng dư",
        "type": "snippet"
    },
    {
        "label": "\\pmod{arg1}",
        "insertText": "\\pmod{${1:arg1}}",
        "detail": "Đồng dư mô-đun",
        "type": "snippet"
    },
    {
        "label": "\\cong",
        "insertText": "\\cong",
        "detail": "Bằng nhau hình học",
        "type": "snippet"
    },
    {
        "label": "\\doteq",
        "insertText": "\\doteq",
        "detail": "Bằng với dấu chấm",
        "type": "snippet"
    },
    {
        "label": "\\asymp",
        "insertText": "\\asymp",
        "detail": "Tiệm cận bằng",
        "type": "snippet"
    },
    {
        "label": "\\perp",
        "insertText": "\\perp",
        "detail": "Vuông góc",
        "type": "snippet"
    },
    {
        "label": "\\parallel",
        "insertText": "\\parallel",
        "detail": "Song song",
        "type": "snippet"
    },
    {
        "label": "\\nparallel",
        "insertText": "\\nparallel",
        "detail": "Không song song",
        "type": "snippet"
    },
    {
        "label": "\\mid",
        "insertText": "\\mid",
        "detail": "Chia hết",
        "type": "snippet"
    },
    {
        "label": "\\nmid",
        "insertText": "\\nmid",
        "detail": "Không chia hết",
        "type": "snippet"
    },
    {
        "label": "\\leqslant",
        "insertText": "\\leqslant",
        "detail": "Nhỏ hơn hoặc bằng nghiêng",
        "type": "snippet"
    },
    {
        "label": "\\geqslant",
        "insertText": "\\geqslant",
        "detail": "Lớn hơn hoặc bằng nghiêng",
        "type": "snippet"
    },
    {
        "label": "\\nless",
        "insertText": "\\nless",
        "detail": "Không nhỏ hơn",
        "type": "snippet"
    },
    {
        "label": "\\ngtr",
        "insertText": "\\ngtr",
        "detail": "Không lớn hơn",
        "type": "snippet"
    },
    {
        "label": "\\nleq",
        "insertText": "\\nleq",
        "detail": "Không nhỏ hơn hoặc bằng",
        "type": "snippet"
    },
    {
        "label": "\\ngeq",
        "insertText": "\\ngeq",
        "detail": "Không lớn hơn hoặc bằng",
        "type": "snippet"
    },
    {
        "label": "\\models",
        "insertText": "\\models",
        "detail": "Mô hình đúng",
        "type": "snippet"
    },
    {
        "label": "\\oplus",
        "insertText": "\\oplus",
        "detail": "Tổng trực tiếp",
        "type": "snippet"
    },
    {
        "label": "\\otimes",
        "insertText": "\\otimes",
        "detail": "Tích trực tiếp",
        "type": "snippet"
    },
    {
        "label": "\\ominus",
        "insertText": "\\ominus",
        "detail": "Trừ vòng tròn",
        "type": "snippet"
    },
    {
        "label": "\\oslash",
        "insertText": "\\oslash",
        "detail": "Chia vòng tròn",
        "type": "snippet"
    },
    {
        "label": "\\odot",
        "insertText": "\\odot",
        "detail": "Chấm vòng tròn",
        "type": "snippet"
    },
    {
        "label": "\\Box",
        "insertText": "\\Box",
        "detail": "Hộp vuông toán tử",
        "type": "snippet"
    },
    {
        "label": "\\boxtimes",
        "insertText": "\\boxtimes",
        "detail": "Hộp nhân toán tử",
        "type": "snippet"
    },
    {
        "label": "\\boxplus",
        "insertText": "\\boxplus",
        "detail": "Hộp cộng",
        "type": "snippet"
    },
    {
        "label": "\\bigwedge",
        "insertText": "\\bigwedge",
        "detail": "Phép hội lớn",
        "type": "snippet"
    },
    {
        "label": "\\bigvee",
        "insertText": "\\bigvee",
        "detail": "Phép tuyển lớn",
        "type": "snippet"
    },
    {
        "label": "\\bigoplus",
        "insertText": "\\bigoplus",
        "detail": "Oplus lớn",
        "type": "snippet"
    },
    {
        "label": "\\bigotimes",
        "insertText": "\\bigotimes",
        "detail": "Otimes lớn",
        "type": "snippet"
    },
    {
        "label": "\\infty",
        "insertText": "\\infty",
        "detail": "Vô cực",
        "type": "snippet"
    },
    {
        "label": "\\forall",
        "insertText": "\\forall",
        "detail": "Với mọi",
        "type": "snippet"
    },
    {
        "label": "\\exists",
        "insertText": "\\exists",
        "detail": "Tồn tại",
        "type": "snippet"
    },
    {
        "label": "\\nexists",
        "insertText": "\\nexists",
        "detail": "Không tồn tại",
        "type": "snippet"
    },
    {
        "label": "\\Re",
        "insertText": "\\Re",
        "detail": "Phần thực",
        "type": "snippet"
    },
    {
        "label": "\\Im",
        "insertText": "\\Im",
        "detail": "Phần ảo",
        "type": "snippet"
    },
    {
        "label": "\\nabla",
        "insertText": "\\nabla",
        "detail": "Toán tử Nabla",
        "type": "snippet"
    },
    {
        "label": "\\partial",
        "insertText": "\\partial",
        "detail": "Đạo hàm riêng",
        "type": "snippet"
    },
    {
        "label": "\\emptyset",
        "insertText": "\\emptyset",
        "detail": "Tập rỗng",
        "type": "snippet"
    },
    {
        "label": "\\varnothing",
        "insertText": "\\varnothing",
        "detail": "Tập rỗng kiểu đẹp",
        "type": "snippet"
    },
    {
        "label": "\\wp",
        "insertText": "\\wp",
        "detail": "Hàm Weierstrass p",
        "type": "snippet"
    },
    {
        "label": "\\complement",
        "insertText": "\\complement",
        "detail": "Phần bù",
        "type": "snippet"
    },
    {
        "label": "\\neg",
        "insertText": "\\neg",
        "detail": "Phủ định",
        "type": "snippet"
    },
    {
        "label": "\\cdots",
        "insertText": "\\cdots",
        "detail": "Ba chấm ngang",
        "type": "snippet"
    },
    {
        "label": "\\square",
        "insertText": "\\square",
        "detail": "Hình vuông trống",
        "type": "snippet"
    },
    {
        "label": "\\blacksquare",
        "insertText": "\\blacksquare",
        "detail": "Hình vuông đen",
        "type": "snippet"
    },
    {
        "label": "\\triangle",
        "insertText": "\\triangle",
        "detail": "Tam giác",
        "type": "snippet"
    },
    {
        "label": "\\surd",
        "insertText": "\\surd",
        "detail": "Biểu tượng dấu căn",
        "type": "snippet"
    },
    {
        "label": "\\dagger",
        "insertText": "\\dagger",
        "detail": "Dấu chữ thập",
        "type": "snippet"
    },
    {
        "label": "\\ddagger",
        "insertText": "\\ddagger",
        "detail": "Dấu chữ thập đôi",
        "type": "snippet"
    },
    {
        "label": "\\prime",
        "insertText": "\\prime",
        "detail": "Dấu phẩy đạo hàm",
        "type": "snippet"
    },
    {
        "label": "\\ell",
        "insertText": "\\ell",
        "detail": "Ký tự l viết tay",
        "type": "snippet"
    },
    {
        "label": "\\hbar",
        "insertText": "\\hbar",
        "detail": "H gạch ngang Planck",
        "type": "snippet"
    },
    {
        "label": "\\imath",
        "insertText": "\\imath",
        "detail": "I không chấm",
        "type": "snippet"
    },
    {
        "label": "\\jmath",
        "insertText": "\\jmath",
        "detail": "J không chấm",
        "type": "snippet"
    },
    {
        "label": "\\aleph",
        "insertText": "\\aleph",
        "detail": "Ký tự Aleph",
        "type": "snippet"
    },
    {
        "label": "\\beth",
        "insertText": "\\beth",
        "detail": "Ký tự Beth",
        "type": "snippet"
    },
    {
        "label": "\\gimel",
        "insertText": "\\gimel",
        "detail": "Ký tự Gimel",
        "type": "snippet"
    },
    {
        "label": "\\angle",
        "insertText": "\\angle",
        "detail": "Góc",
        "type": "snippet"
    },
    {
        "label": "\\measuredangle",
        "insertText": "\\measuredangle",
        "detail": "Góc đo được",
        "type": "snippet"
    },
    {
        "label": "\\sphericalangle",
        "insertText": "\\sphericalangle",
        "detail": "Góc cầu",
        "type": "snippet"
    },
    {
        "label": "\\therefore",
        "insertText": "\\therefore",
        "detail": "Vì vậy",
        "type": "snippet"
    },
    {
        "label": "\\because",
        "insertText": "\\because",
        "detail": "Bởi vì",
        "type": "snippet"
    },
    {
        "label": "\\propto",
        "insertText": "\\propto",
        "detail": "Tỉ lệ thuận",
        "type": "snippet"
    },
    {
        "label": "\\not",
        "insertText": "\\not",
        "detail": "Phủ định ký hiệu",
        "type": "snippet"
    },
    {
        "label": "\\vdots",
        "insertText": "\\vdots",
        "detail": "Dấu chấm lửng dọc",
        "type": "snippet"
    },
    {
        "label": "\\ddots",
        "insertText": "\\ddots",
        "detail": "Dấu chấm lửng chéo",
        "type": "snippet"
    },
    {
        "label": "\\hat{arg1}",
        "insertText": "\\hat{${1:arg1}}",
        "detail": "Dấu mũ nón",
        "type": "snippet"
    },
    {
        "label": "\\bar{arg1}",
        "insertText": "\\bar{${1:arg1}}",
        "detail": "Gạch ngang trên",
        "type": "snippet"
    },
    {
        "label": "\\tilde{arg1}",
        "insertText": "\\tilde{${1:arg1}}",
        "detail": "Dấu ngã",
        "type": "snippet"
    },
    {
        "label": "\\vec{arg1}",
        "insertText": "\\vec{${1:arg1}}",
        "detail": "Mũi tên vector",
        "type": "snippet"
    },
    {
        "label": "\\dot{arg1}",
        "insertText": "\\dot{${1:arg1}}",
        "detail": "Dấu chấm trên",
        "type": "snippet"
    },
    {
        "label": "\\ddot{arg1}",
        "insertText": "\\ddot{${1:arg1}}",
        "detail": "Hai chấm trên",
        "type": "snippet"
    },
    {
        "label": "\\dddot{arg1}",
        "insertText": "\\dddot{${1:arg1}}",
        "detail": "Ba chấm trên",
        "type": "snippet"
    },
    {
        "label": "\\grave{arg1}",
        "insertText": "\\grave{${1:arg1}}",
        "detail": "Dấu huyền (toán)",
        "type": "snippet"
    },
    {
        "label": "\\acute{arg1}",
        "insertText": "\\acute{${1:arg1}}",
        "detail": "Dấu sắc (toán)",
        "type": "snippet"
    },
    {
        "label": "\\breve{arg1}",
        "insertText": "\\breve{${1:arg1}}",
        "detail": "Dấu bằng ngắn",
        "type": "snippet"
    },
    {
        "label": "\\widehat{arg1}",
        "insertText": "\\widehat{${1:arg1}}",
        "detail": "Dấu mũ rộng",
        "type": "snippet"
    },
    {
        "label": "\\widetilde{arg1}",
        "insertText": "\\widetilde{${1:arg1}}",
        "detail": "Dấu ngã rộng",
        "type": "snippet"
    },
    {
        "label": "\\overbrace{arg1}",
        "insertText": "\\overbrace{${1:arg1}}",
        "detail": "Ngoặc trên",
        "type": "snippet"
    },
    {
        "label": "\\underbrace{arg1}",
        "insertText": "\\underbrace{${1:arg1}}",
        "detail": "Ngoặc dưới",
        "type": "snippet"
    },
    {
        "label": "\\overleftarrow{arg1}",
        "insertText": "\\overleftarrow{${1:arg1}}",
        "detail": "Mũi tên trái bên trên",
        "type": "snippet"
    },
    {
        "label": "\\overrightarrow{arg1}",
        "insertText": "\\overrightarrow{${1:arg1}}",
        "detail": "Mũi tên phải bên trên",
        "type": "snippet"
    },
    {
        "label": "\\overleftrightarrow{arg1}",
        "insertText": "\\overleftrightarrow{${1:arg1}}",
        "detail": "Mũi tên hai chiều trên",
        "type": "snippet"
    },
    {
        "label": "\\overset{arg1}{arg2}",
        "insertText": "\\overset{${1:arg1}}{${2:arg2}}",
        "detail": "Ký hiệu trên ký hiệu",
        "type": "snippet"
    },
    {
        "label": "\\underset{arg1}{arg2}",
        "insertText": "\\underset{${1:arg1}}{${2:arg2}}",
        "detail": "Ký hiệu dưới ký hiệu",
        "type": "snippet"
    },
    {
        "label": "\\stackrel{arg1}{arg2}",
        "insertText": "\\stackrel{${1:arg1}}{${2:arg2}}",
        "detail": "Xếp chồng quan hệ",
        "type": "snippet"
    },
    {
        "label": "\\boldsymbol{arg1}",
        "insertText": "\\boldsymbol{${1:arg1}}",
        "detail": "Ký hiệu đậm toán học",
        "type": "snippet"
    },
    {
        "label": "\\quad",
        "insertText": "\\quad",
        "detail": "Khoảng cách rộng",
        "type": "snippet"
    },
    {
        "label": "\\qquad",
        "insertText": "\\qquad",
        "detail": "Khoảng cách rất rộng",
        "type": "snippet"
    },
    {
        "label": "\\,",
        "insertText": "\\,",
        "detail": "Khoảng cách nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\:",
        "insertText": "\\:",
        "detail": "Khoảng cách vừa",
        "type": "snippet"
    },
    {
        "label": "\\",
        "insertText": "\\ ",
        "detail": "Khoảng trắng văn bản",
        "type": "snippet"
    },
    {
        "label": "\\mathrel",
        "insertText": "\\mathrel",
        "detail": "Khoảng cách quan hệ",
        "type": "snippet"
    },
    {
        "label": "\\mathbin",
        "insertText": "\\mathbin",
        "detail": "Khoảng cách nhị phân",
        "type": "snippet"
    },
    {
        "label": "\\displaystyle",
        "insertText": "\\displaystyle",
        "detail": "Kiểu hiển thị",
        "type": "snippet"
    },
    {
        "label": "\\textstyle",
        "insertText": "\\textstyle",
        "detail": "Kiểu trong dòng",
        "type": "snippet"
    },
    {
        "label": "\\scriptstyle",
        "insertText": "\\scriptstyle",
        "detail": "Kiểu chỉ số",
        "type": "snippet"
    },
    {
        "label": "\\scriptscriptstyle",
        "insertText": "\\scriptscriptstyle",
        "detail": "Kiểu chỉ số nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\mathbb{math}",
        "insertText": "\\mathbb{${1:math}}",
        "detail": "Chữ rỗng hoa",
        "type": "snippet"
    },
    {
        "label": "\\mathscr{math}",
        "insertText": "\\mathscr{${1:math}}",
        "detail": "Chữ Script hoa mỹ",
        "type": "snippet"
    },
    {
        "label": "\\mathcal{math}",
        "insertText": "\\mathcal{${1:math}}",
        "detail": "Chữ hoa mỹ cơ bản",
        "type": "snippet"
    },
    {
        "label": "\\mathfrak{math}",
        "insertText": "\\mathfrak{${1:math}}",
        "detail": "Chữ cổ",
        "type": "snippet"
    },
    {
        "label": "\\mathrm{math}",
        "insertText": "\\mathrm{${1:math}}",
        "detail": "Chữ đứng",
        "type": "snippet"
    },
    {
        "label": "\\mathit{math}",
        "insertText": "\\mathit{${1:math}}",
        "detail": "Chữ nghiêng",
        "type": "snippet"
    },
    {
        "label": "\\mathbf{math}",
        "insertText": "\\mathbf{${1:math}}",
        "detail": "Chữ đậm",
        "type": "snippet"
    },
    {
        "label": "\\mathsf{math}",
        "insertText": "\\mathsf{${1:math}}",
        "detail": "Chữ không chân",
        "type": "snippet"
    },
    {
        "label": "\\mathtt{math}",
        "insertText": "\\mathtt{${1:math}}",
        "detail": "Chữ máy đánh",
        "type": "snippet"
    },
    {
        "label": "\\mathnormal{arg1}",
        "insertText": "\\mathnormal{${1:arg1}}",
        "detail": "Chữ thường toán học",
        "type": "snippet"
    },
    {
        "label": "\\operatorname{arg1}",
        "insertText": "\\operatorname{${1:arg1}}",
        "detail": "Toán tử mới không có dấu",
        "type": "snippet"
    },
    {
        "label": "\\toprule",
        "insertText": "\\toprule",
        "detail": "Đường kẻ trên đầu bảng",
        "type": "snippet"
    },
    {
        "label": "\\midrule",
        "insertText": "\\midrule",
        "detail": "Đường kẻ giữa tiêu đề",
        "type": "snippet"
    },
    {
        "label": "\\bottomrule",
        "insertText": "\\bottomrule",
        "detail": "Đường kẻ cuối bảng",
        "type": "snippet"
    },
    {
        "label": "\\addlinespace",
        "insertText": "\\addlinespace",
        "detail": "Thêm khoảng trống dòng",
        "type": "snippet"
    },
    {
        "label": "\\specialrule{w}{a}{b}",
        "insertText": "\\specialrule{w}{a}{b}",
        "detail": "Đường kẻ ngang mảnh",
        "type": "snippet"
    },
    {
        "label": "\\\\",
        "insertText": "\\\\",
        "detail": "Kết thúc hàng",
        "type": "snippet"
    },
    {
        "label": "\\[...]",
        "insertText": "\\[...]",
        "detail": "Kết thúc hàng giãn",
        "type": "snippet"
    },
    {
        "label": "\\hline",
        "insertText": "\\hline",
        "detail": "Đường kẻ ngang",
        "type": "snippet"
    },
    {
        "label": "\\hline\\hline",
        "insertText": "\\hline\\hline",
        "detail": "Đường kẻ ngang kép",
        "type": "snippet"
    },
    {
        "label": "\\cline{i-j}",
        "insertText": "\\cline{i-j}",
        "detail": "Đường kẻ ngang một phần",
        "type": "snippet"
    },
    {
        "label": "\\newline",
        "insertText": "\\newline",
        "detail": "Xuống dòng trong ô",
        "type": "snippet"
    },
    {
        "label": "\\multicolumn{cols}{pos}{text}",
        "insertText": "\\multicolumn{cols}{pos}{text}",
        "detail": "Gộp cột",
        "type": "snippet"
    },
    {
        "label": "\\multirow{rows}{width}{text}",
        "insertText": "\\multirow{rows}{width}{text}",
        "detail": "Gộp hàng",
        "type": "snippet"
    },
    {
        "label": "\\endfirsthead",
        "insertText": "\\endfirsthead",
        "detail": "Kết thúc đầu trang đầu tiên",
        "type": "snippet"
    },
    {
        "label": "\\endhead",
        "insertText": "\\endhead",
        "detail": "Kết thúc đầu trang lặp lại",
        "type": "snippet"
    },
    {
        "label": "\\endfoot",
        "insertText": "\\endfoot",
        "detail": "Kết thúc chân trang lặp lại",
        "type": "snippet"
    },
    {
        "label": "\\endlastfoot",
        "insertText": "\\endlastfoot",
        "detail": "Kết thúc chân trang cuối cùng",
        "type": "snippet"
    },
    {
        "label": "\\centering",
        "insertText": "\\centering",
        "detail": "Lệnh căn giữa",
        "type": "snippet"
    },
    {
        "label": "\\caption{text}",
        "insertText": "\\caption{${1:text}}",
        "detail": "Chú thích hình bảng",
        "type": "snippet"
    },
    {
        "label": "\\label{marker}",
        "insertText": "\\label{${1:marker}}",
        "detail": "Gán nhãn tham chiếu",
        "type": "snippet"
    },
    {
        "label": "\\ref{marker}",
        "insertText": "\\ref{${1:marker}}",
        "detail": "Tham chiếu",
        "type": "snippet"
    },
    {
        "label": "\\listoftables",
        "insertText": "\\listoftables",
        "detail": "Danh sách bảng",
        "type": "snippet"
    },
    {
        "label": "\\listoffigures",
        "insertText": "\\listoffigures",
        "detail": "Danh sách hình",
        "type": "snippet"
    },
    {
        "label": "\\renewcommand{\\\\command}{definition}",
        "insertText": "\\renewcommand{\\\\${1:command}}{${2:definition}}",
        "detail": "Đổi tên danh sách bảng",
        "type": "snippet"
    },
    {
        "label": "\\thispagestyle{empty}",
        "insertText": "\\thispagestyle{empty}",
        "detail": "Không đánh số trang",
        "type": "snippet"
    },
    {
        "label": "\\pagenumbering{arg1}",
        "insertText": "\\pagenumbering{${1:arg1}}",
        "detail": "Kiểu đánh số trang",
        "type": "snippet"
    },
    {
        "label": "\\setlength{\\\\length}{value}",
        "insertText": "\\setlength{\\\\${1:length}}{${2:value}}",
        "detail": "Độ dày đường kẻ bảng",
        "type": "snippet"
    },
    {
        "label": "\\rowcolors{start}{odd}{even}",
        "insertText": "\\rowcolors{start}{odd}{even}",
        "detail": "Màu hàng xen kẽ",
        "type": "snippet"
    },
    {
        "label": "\\arrayrulecolor{arg1}",
        "insertText": "\\arrayrulecolor{${1:arg1}}",
        "detail": "Màu đường kẻ",
        "type": "snippet"
    },
    {
        "label": "\\cellcolor{arg1}",
        "insertText": "\\cellcolor{${1:arg1}}",
        "detail": "Màu nền ô",
        "type": "snippet"
    },
    {
        "label": "\\rowcolor{arg1}",
        "insertText": "\\rowcolor{${1:arg1}}",
        "detail": "Màu nền hàng",
        "type": "snippet"
    },
    {
        "label": "\\newcolumntype{arg1}{arg2}",
        "insertText": "\\newcolumntype{${1:arg1}}{${2:arg2}}",
        "detail": "Định nghĩa kiểu cột mới",
        "type": "snippet"
    },
    {
        "label": "\\columncolor{arg1}",
        "insertText": "\\columncolor{${1:arg1}}",
        "detail": "Màu nền cột",
        "type": "snippet"
    },
    {
        "label": "\\columnsep",
        "insertText": "\\columnsep",
        "detail": "Khoảng cách giữa các cột",
        "type": "snippet"
    },
    {
        "label": "\\columnwidth",
        "insertText": "\\columnwidth",
        "detail": "Độ rộng cột hiện tại",
        "type": "snippet"
    },
    {
        "label": "\\linewidth",
        "insertText": "\\linewidth",
        "detail": "Độ rộng dòng hiện tại",
        "type": "snippet"
    },
    {
        "label": "\\paperwidth",
        "insertText": "\\paperwidth",
        "detail": "Độ rộng trang giấy",
        "type": "snippet"
    },
    {
        "label": "\\paperheight",
        "insertText": "\\paperheight",
        "detail": "Chiều cao trang giấy",
        "type": "snippet"
    },
    {
        "label": "\\textwidth",
        "insertText": "\\textwidth",
        "detail": "Độ rộng văn bản",
        "type": "snippet"
    },
    {
        "label": "\\textheight",
        "insertText": "\\textheight",
        "detail": "Chiều cao văn bản",
        "type": "snippet"
    },
    {
        "label": "\\dv{f}{x}",
        "insertText": "\\dv{f}{x}",
        "detail": "Đạo hàm hàm số",
        "type": "snippet"
    },
    {
        "label": "\\pdv{f}{x}",
        "insertText": "\\pdv{f}{x}",
        "detail": "Đạo hàm riêng",
        "type": "snippet"
    },
    {
        "label": "\\grad",
        "insertText": "\\grad",
        "detail": "Véctơ Gradient",
        "type": "snippet"
    },
    {
        "label": "\\curl",
        "insertText": "\\curl",
        "detail": "Toán tử rô-ta",
        "type": "snippet"
    },
    {
        "label": "\\laplacian",
        "insertText": "\\laplacian",
        "detail": "Toán tử Laplace",
        "type": "snippet"
    },
    {
        "label": "\\bra{arg1}",
        "insertText": "\\bra{${1:arg1}}",
        "detail": "Ký hiệu Bra",
        "type": "snippet"
    },
    {
        "label": "\\ket{arg1}",
        "insertText": "\\ket{${1:arg1}}",
        "detail": "Ký hiệu Ket",
        "type": "snippet"
    },
    {
        "label": "\\braket{arg1}{arg2}",
        "insertText": "\\braket{${1:arg1}}{${2:arg2}}",
        "detail": "Ký hiệu ngoặc Dirac",
        "type": "snippet"
    },
    {
        "label": "\\SI{arg1}{arg2}",
        "insertText": "\\SI{${1:arg1}}{${2:arg2}}",
        "detail": "Viết số và đơn vị",
        "type": "snippet"
    },
    {
        "label": "\\si{arg1}",
        "insertText": "\\si{${1:arg1}}",
        "detail": "Viết đơn vị riêng",
        "type": "snippet"
    },
    {
        "label": "\\num{arg1}",
        "insertText": "\\num{${1:arg1}}",
        "detail": "Viết số riêng",
        "type": "snippet"
    },
    {
        "label": "\\metre",
        "insertText": "\\metre",
        "detail": "Đơn vị mét",
        "type": "snippet"
    },
    {
        "label": "\\second",
        "insertText": "\\second",
        "detail": "Đơn vị giây",
        "type": "snippet"
    },
    {
        "label": "\\kilogram",
        "insertText": "\\kilogram",
        "detail": "Đơn vị kilôgam",
        "type": "snippet"
    },
    {
        "label": "\\ampere",
        "insertText": "\\ampere",
        "detail": "Đơn vị Ampe",
        "type": "snippet"
    },
    {
        "label": "\\kelvin",
        "insertText": "\\kelvin",
        "detail": "Đơn vị Kelvin",
        "type": "snippet"
    },
    {
        "label": "\\candela",
        "insertText": "\\candela",
        "detail": "Đơn vị Candela",
        "type": "snippet"
    },
    {
        "label": "\\mole",
        "insertText": "\\mole",
        "detail": "Đơn vị Mol",
        "type": "snippet"
    },
    {
        "label": "\\newton",
        "insertText": "\\newton",
        "detail": "Đơn vị Newton",
        "type": "snippet"
    },
    {
        "label": "\\pascal",
        "insertText": "\\pascal",
        "detail": "Đơn vị Pascal",
        "type": "snippet"
    },
    {
        "label": "\\celsius",
        "insertText": "\\celsius",
        "detail": "Đơn vị độ C",
        "type": "snippet"
    },
    {
        "label": "\\degree",
        "insertText": "\\degree",
        "detail": "Đơn vị độ",
        "type": "snippet"
    },
    {
        "label": "\\percent",
        "insertText": "\\percent",
        "detail": "Phần trăm siunitx",
        "type": "snippet"
    },
    {
        "label": "\\qtyrange{arg1}{arg2}arg3",
        "insertText": "\\qtyrange{${1:arg1}}{${2:arg2}}${3:arg3}",
        "detail": "Viết dải giá trị",
        "type": "snippet"
    },
    {
        "label": "\\qtylist{arg1}{arg2}",
        "insertText": "\\qtylist{${1:arg1}}{${2:arg2}}",
        "detail": "Viết danh sách giá trị",
        "type": "snippet"
    },
    {
        "label": "\\squared",
        "insertText": "\\squared",
        "detail": "Số mũ bình phương",
        "type": "snippet"
    },
    {
        "label": "\\cubed",
        "insertText": "\\cubed",
        "detail": "Số mũ lập phương",
        "type": "snippet"
    },
    {
        "label": "\\per",
        "insertText": "\\per",
        "detail": "Lệnh trên mỗi đơn vị",
        "type": "snippet"
    },
    {
        "label": "\\graphicspath{arg1}",
        "insertText": "\\graphicspath{${1:arg1}}",
        "detail": "Đường dẫn thư mục ảnh",
        "type": "snippet"
    },
    {
        "label": "\\includegraphics[options]{image_path}",
        "insertText": "\\includegraphics[${1:options}]{${2:image_path}}",
        "detail": "Chèn hình ảnh",
        "type": "snippet"
    },
    {
        "label": "\\includepdf{arg1}",
        "insertText": "\\includepdf{${1:arg1}}",
        "detail": "Nhập trang PDF",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{positioning}",
        "insertText": "\\usetikzlibrary{positioning}",
        "detail": "Thư viện vị trí",
        "type": "snippet"
    },
    {
        "label": "\\draw",
        "insertText": "\\draw",
        "detail": "Lệnh vẽ đường",
        "type": "snippet"
    },
    {
        "label": "\\fill",
        "insertText": "\\fill",
        "detail": "Lệnh tô màu",
        "type": "snippet"
    },
    {
        "label": "\\filldraw",
        "insertText": "\\filldraw",
        "detail": "Vẽ và tô màu",
        "type": "snippet"
    },
    {
        "label": "\\node",
        "insertText": "\\node",
        "detail": "Điểm văn bản",
        "type": "snippet"
    },
    {
        "label": "\\coordinate",
        "insertText": "\\coordinate",
        "detail": "Tọa độ điểm",
        "type": "snippet"
    },
    {
        "label": "\\path",
        "insertText": "\\path",
        "detail": "Lệnh đường dẫn",
        "type": "snippet"
    },
    {
        "label": "\\put(x,y)arg1",
        "insertText": "\\put(x,y)${1:arg1}",
        "detail": "Đặt đối tượng",
        "type": "snippet"
    },
    {
        "label": "\\multiput(x,y)(dx,dy){n}{arg1}",
        "insertText": "\\multiput(x,y)(dx,dy){n}{${1:arg1}}",
        "detail": "Đặt đối tượng lặp lại",
        "type": "snippet"
    },
    {
        "label": "\\linethickness{arg1}",
        "insertText": "\\linethickness{${1:arg1}}",
        "detail": "Độ dày nét vẽ Picture",
        "type": "snippet"
    },
    {
        "label": "\\thicklines",
        "insertText": "\\thicklines",
        "detail": "Nét đậm Picture",
        "type": "snippet"
    },
    {
        "label": "\\thinlines",
        "insertText": "\\thinlines",
        "detail": "Nét mảnh Picture",
        "type": "snippet"
    },
    {
        "label": "\\line(x,y){len}",
        "insertText": "\\line(x,y){len}",
        "detail": "Đường thẳng hướng",
        "type": "snippet"
    },
    {
        "label": "\\vector(x,y){len}",
        "insertText": "\\vector(x,y){len}",
        "detail": "Mũi tên vector",
        "type": "snippet"
    },
    {
        "label": "\\circle{diam}",
        "insertText": "\\circle{diam}",
        "detail": "Hình tròn đường biên",
        "type": "snippet"
    },
    {
        "label": "\\circle*{diam}",
        "insertText": "\\circle*{diam}",
        "detail": "Hình tròn tô đặc",
        "type": "snippet"
    },
    {
        "label": "\\oval(w,h)[options]",
        "insertText": "\\oval(w,h)[${1:options}]",
        "detail": "Hình Oval",
        "type": "snippet"
    },
    {
        "label": "\\qbezier(x1,y1)(x,y)(x2,y2)",
        "insertText": "\\qbezier(x1,y1)(x,y)(x2,y2)",
        "detail": "Đường cong Picture",
        "type": "snippet"
    },
    {
        "label": "\\foreach \\x in {1,...,n} arg1",
        "insertText": "\\foreach \\x in {1,...,n} ${1:arg1}",
        "detail": "Lặp lại",
        "type": "snippet"
    },
    {
        "label": "\\clip",
        "insertText": "\\clip",
        "detail": "Cắt vùng vẽ",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{arrows.meta}",
        "insertText": "\\usetikzlibrary{arrows.meta}",
        "detail": "Thư viện mũi tên mới",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{decorations.pathmorphing}",
        "insertText": "\\usetikzlibrary{decorations.pathmorphing}",
        "detail": "Thư viện trang trí",
        "type": "snippet"
    },
    {
        "label": "\\pageref{marker}",
        "insertText": "\\pageref{${1:marker}}",
        "detail": "Tham chiếu trang",
        "type": "snippet"
    },
    {
        "label": "\\href{url}{text}",
        "insertText": "\\href{${1:url}}{${2:text}}",
        "detail": "Liên kết Web ẩn",
        "type": "snippet"
    },
    {
        "label": "\\url{url}",
        "insertText": "\\url{${1:url}}",
        "detail": "Liên kết Web hiện",
        "type": "snippet"
    },
    {
        "label": "\\hyperlink{name}{text}",
        "insertText": "\\hyperlink{name}{text}",
        "detail": "Liên kết nội bộ",
        "type": "snippet"
    },
    {
        "label": "\\hypertarget{name}{text}",
        "insertText": "\\hypertarget{name}{text}",
        "detail": "Điểm neo liên kết",
        "type": "snippet"
    },
    {
        "label": "\\hypersetup{arg1}",
        "insertText": "\\hypersetup{${1:arg1}}",
        "detail": "Cấu hình liên kết",
        "type": "snippet"
    },
    {
        "label": "\\cite{key}",
        "insertText": "\\cite{${1:key}}",
        "detail": "Trích dẫn tài liệu",
        "type": "snippet"
    },
    {
        "label": "\\bibitem{key}",
        "insertText": "\\bibitem{${1:key}}",
        "detail": "Mục tài liệu tham khảo",
        "type": "snippet"
    },
    {
        "label": "\\bibliographystyle{arg1}",
        "insertText": "\\bibliographystyle{${1:arg1}}",
        "detail": "Kiểu hiển thị tham khảo",
        "type": "snippet"
    },
    {
        "label": "\\bibliography{arg1}",
        "insertText": "\\bibliography{${1:arg1}}",
        "detail": "Chèn file dữ liệu tham khảo",
        "type": "snippet"
    },
    {
        "label": "\\makeglossaries",
        "insertText": "\\makeglossaries",
        "detail": "Tạo bảng chú giải",
        "type": "snippet"
    },
    {
        "label": "\\newglossaryentry{arg1}{arg2}",
        "insertText": "\\newglossaryentry{${1:arg1}}{${2:arg2}}",
        "detail": "Định nghĩa từ mới",
        "type": "snippet"
    },
    {
        "label": "\\newacronym{arg1}{arg2}arg3",
        "insertText": "\\newacronym{${1:arg1}}{${2:arg2}}${3:arg3}",
        "detail": "Định nghĩa từ viết tắt",
        "type": "snippet"
    },
    {
        "label": "\\gls{arg1}",
        "insertText": "\\gls{${1:arg1}}",
        "detail": "Sử dụng từ thường",
        "type": "snippet"
    },
    {
        "label": "\\Gls{arg1}",
        "insertText": "\\Gls{${1:arg1}}",
        "detail": "Sử dụng từ viết hoa",
        "type": "snippet"
    },
    {
        "label": "\\glspl{arg1}",
        "insertText": "\\glspl{${1:arg1}}",
        "detail": "Sử dụng từ số nhiều",
        "type": "snippet"
    },
    {
        "label": "\\printglossaries",
        "insertText": "\\printglossaries",
        "detail": "In bảng chú giải",
        "type": "snippet"
    },
    {
        "label": "\\printglossary[type=\\acronymtype]",
        "insertText": "\\printglossary[type=\\acronymtype]",
        "detail": "In danh sách viết tắt",
        "type": "snippet"
    },
    {
        "label": "\\makenomenclature",
        "insertText": "\\makenomenclature",
        "detail": "Tạo danh mục ký hiệu",
        "type": "snippet"
    },
    {
        "label": "\\nomenclature{arg1}{arg2}",
        "insertText": "\\nomenclature{${1:arg1}}{${2:arg2}}",
        "detail": "Thêm ký hiệu vào danh mục",
        "type": "snippet"
    },
    {
        "label": "\\printnomenclature",
        "insertText": "\\printnomenclature",
        "detail": "In danh mục ký hiệu",
        "type": "snippet"
    },
    {
        "label": "\\makeindex",
        "insertText": "\\makeindex",
        "detail": "Kích hoạt tạo chỉ mục",
        "type": "snippet"
    },
    {
        "label": "\\index{arg1}",
        "insertText": "\\index{${1:arg1}}",
        "detail": "Thêm từ vào chỉ mục",
        "type": "snippet"
    },
    {
        "label": "\\printindex",
        "insertText": "\\printindex",
        "detail": "In bảng chỉ mục",
        "type": "snippet"
    },
    {
        "label": "\\footnote{arg1}",
        "insertText": "\\footnote{${1:arg1}}",
        "detail": "Chú thích chân trang",
        "type": "snippet"
    },
    {
        "label": "\\footnotemark",
        "insertText": "\\footnotemark",
        "detail": "Đánh dấu chú thích bảng",
        "type": "snippet"
    },
    {
        "label": "\\footnotetext{arg1}",
        "insertText": "\\footnotetext{${1:arg1}}",
        "detail": "Nội dung chú thích bảng",
        "type": "snippet"
    },
    {
        "label": "\\addtolength{\\\\length}{value}",
        "insertText": "\\addtolength{\\\\${1:length}}{${2:value}}",
        "detail": "Thêm độ dài",
        "type": "snippet"
    },
    {
        "label": "\\parindent",
        "insertText": "\\parindent",
        "detail": "Khoảng thụt đầu dòng",
        "type": "snippet"
    },
    {
        "label": "\\parskip",
        "insertText": "\\parskip",
        "detail": "Khoảng cách đoạn văn",
        "type": "snippet"
    },
    {
        "label": "\\AtBeginDocument{arg1}",
        "insertText": "\\AtBeginDocument{${1:arg1}}",
        "detail": "Hành động trước văn bản",
        "type": "snippet"
    },
    {
        "label": "\\newpage",
        "insertText": "\\newpage",
        "detail": "Ngắt trang",
        "type": "snippet"
    },
    {
        "label": "\\clearpage",
        "insertText": "\\clearpage",
        "detail": "Xóa trang",
        "type": "snippet"
    },
    {
        "label": "\\hspace{len}",
        "insertText": "\\hspace{len}",
        "detail": "Khoảng trắng ngang",
        "type": "snippet"
    },
    {
        "label": "\\hfill",
        "insertText": "\\hfill",
        "detail": "Khoảng trắng ngang giãn",
        "type": "snippet"
    },
    {
        "label": "\\vspace{len}",
        "insertText": "\\vspace{len}",
        "detail": "Khoảng trắng dọc",
        "type": "snippet"
    },
    {
        "label": "\\vfill",
        "insertText": "\\vfill",
        "detail": "Khoảng trắng dọc giãn",
        "type": "snippet"
    },
    {
        "label": "\\smallskip",
        "insertText": "\\smallskip",
        "detail": "Khoảng dọc nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\medskip",
        "insertText": "\\medskip",
        "detail": "Khoảng dọc vừa",
        "type": "snippet"
    },
    {
        "label": "\\bigskip",
        "insertText": "\\bigskip",
        "detail": "Khoảng dọc lớn",
        "type": "snippet"
    },
    {
        "label": "\\raggedright",
        "insertText": "\\raggedright",
        "detail": "Lệnh căn trái",
        "type": "snippet"
    },
    {
        "label": "\\raggedleft",
        "insertText": "\\raggedleft",
        "detail": "Lệnh căn phải",
        "type": "snippet"
    },
    {
        "label": "\\justifying",
        "insertText": "\\justifying",
        "detail": "Căn đều hai bên",
        "type": "snippet"
    },
    {
        "label": "\\sout{arg1}",
        "insertText": "\\sout{${1:arg1}}",
        "detail": "Gạch ngang văn bản",
        "type": "snippet"
    },
    {
        "label": "\\xout{arg1}",
        "insertText": "\\xout{${1:arg1}}",
        "detail": "Gạch chéo xóa chữ",
        "type": "snippet"
    },
    {
        "label": "\\dashuline{arg1}",
        "insertText": "\\dashuline{${1:arg1}}",
        "detail": "Gạch dưới nét đứt",
        "type": "snippet"
    },
    {
        "label": "\\hl{arg1}",
        "insertText": "\\hl{${1:arg1}}",
        "detail": "Tô vàng văn bản",
        "type": "snippet"
    },
    {
        "label": "\\st{arg1}",
        "insertText": "\\st{${1:arg1}}",
        "detail": "Gạch ngang chữ",
        "type": "snippet"
    },
    {
        "label": "\\ul{arg1}",
        "insertText": "\\ul{${1:arg1}}",
        "detail": "Gạch chân chữ",
        "type": "snippet"
    },
    {
        "label": "\\so{arg1}",
        "insertText": "\\so{${1:arg1}}",
        "detail": "Giãn cách chữ",
        "type": "snippet"
    },
    {
        "label": "\\titleformat{section}{arg1}arg2arg3arg4",
        "insertText": "\\titleformat{section}{${1:arg1}}${2:arg2}{${3:arg3}}${4:arg4}",
        "detail": "Định dạng tiêu đề mục",
        "type": "snippet"
    },
    {
        "label": "\\titlespacing*{section}{0pt}{*2}{*1}",
        "insertText": "\\titlespacing*{section}{0pt}{*2}{*1}",
        "detail": "Khoảng cách tiêu đề mục",
        "type": "snippet"
    },
    {
        "label": "\\singlespacing",
        "insertText": "\\singlespacing",
        "detail": "Giãn dòng đơn",
        "type": "snippet"
    },
    {
        "label": "\\onehalfspacing",
        "insertText": "\\onehalfspacing",
        "detail": "Giãn dòng 1.5",
        "type": "snippet"
    },
    {
        "label": "\\doublespacing",
        "insertText": "\\doublespacing",
        "detail": "Giãn dòng đôi",
        "type": "snippet"
    },
    {
        "label": "\\setstretch{val}",
        "insertText": "\\setstretch{val}",
        "detail": "Giãn dòng tùy chỉnh",
        "type": "snippet"
    },
    {
        "label": "\\geometry{margin=1in}",
        "insertText": "\\geometry{margin=1in}",
        "detail": "Thiết lập lề nhanh",
        "type": "snippet"
    },
    {
        "label": "\\geometry{a4paper}",
        "insertText": "\\geometry{a4paper}",
        "detail": "Khổ giấy A4",
        "type": "snippet"
    },
    {
        "label": "\\geometry{landscape}",
        "insertText": "\\geometry{landscape}",
        "detail": "Khổ giấy ngang",
        "type": "snippet"
    },
    {
        "label": "\\layout",
        "insertText": "\\layout",
        "detail": "Hiển thị bố cục",
        "type": "snippet"
    },
    {
        "label": "\\columnbreak",
        "insertText": "\\columnbreak",
        "detail": "Ngắt cột",
        "type": "snippet"
    },
    {
        "label": "\\pagestyle{fancy}",
        "insertText": "\\pagestyle{fancy}",
        "detail": "Kích hoạt kiểu trang Fancy",
        "type": "snippet"
    },
    {
        "label": "\\lhead{text}",
        "insertText": "\\lhead{text}",
        "detail": "Đầu trang bên trái",
        "type": "snippet"
    },
    {
        "label": "\\chead{text}",
        "insertText": "\\chead{text}",
        "detail": "Đầu trang ở giữa",
        "type": "snippet"
    },
    {
        "label": "\\rhead{text}",
        "insertText": "\\rhead{text}",
        "detail": "Đầu trang bên phải",
        "type": "snippet"
    },
    {
        "label": "\\lfoot{text}",
        "insertText": "\\lfoot{text}",
        "detail": "Chân trang bên trái",
        "type": "snippet"
    },
    {
        "label": "\\cfoot{text}",
        "insertText": "\\cfoot{text}",
        "detail": "Chân trang ở giữa",
        "type": "snippet"
    },
    {
        "label": "\\rfoot{text}",
        "insertText": "\\rfoot{text}",
        "detail": "Chân trang bên phải",
        "type": "snippet"
    },
    {
        "label": "\\pagenumbering{arabic}",
        "insertText": "\\pagenumbering{arabic}",
        "detail": "Đánh số Ả Rập",
        "type": "snippet"
    },
    {
        "label": "\\pagenumbering{roman}",
        "insertText": "\\pagenumbering{roman}",
        "detail": "Đánh số La Mã thường",
        "type": "snippet"
    },
    {
        "label": "\\pagenumbering{Roman}",
        "insertText": "\\pagenumbering{Roman}",
        "detail": "Đánh số La Mã hoa",
        "type": "snippet"
    },
    {
        "label": "\\pagenumbering{alph}",
        "insertText": "\\pagenumbering{alph}",
        "detail": "Đánh số chữ cái",
        "type": "snippet"
    },
    {
        "label": "\\setcounter{counter}{value}",
        "insertText": "\\setcounter{${1:counter}}{${2:value}}",
        "detail": "Đặt lại số trang",
        "type": "snippet"
    },
    {
        "label": "\\color{name}",
        "insertText": "\\color{name}",
        "detail": "Màu văn bản",
        "type": "snippet"
    },
    {
        "label": "\\textcolor{color}{text}",
        "insertText": "\\textcolor{${1:color}}{${2:text}}",
        "detail": "Màu đoạn văn bản",
        "type": "snippet"
    },
    {
        "label": "\\colorbox{color}{text}",
        "insertText": "\\colorbox{${1:color}}{${2:text}}",
        "detail": "Màu nền văn bản",
        "type": "snippet"
    },
    {
        "label": "\\pagecolor{color}",
        "insertText": "\\pagecolor{${1:color}}",
        "detail": "Màu nền trang",
        "type": "snippet"
    },
    {
        "label": "\\definecolor{name}{model}{spec}",
        "insertText": "\\definecolor{${1:name}}{${2:model}}{${3:spec}}",
        "detail": "Định nghĩa màu mới",
        "type": "snippet"
    },
    {
        "label": "\\verb|...|",
        "insertText": "\\verb|...|",
        "detail": "Nguyên văn trong dòng",
        "type": "snippet"
    },
    {
        "label": "\\lstset{language=Python}",
        "insertText": "\\lstset{language=Python}",
        "detail": "Thiết lập ngôn ngữ",
        "type": "snippet"
    },
    {
        "label": "\\lstinputlisting{file}",
        "insertText": "\\lstinputlisting{file}",
        "detail": "Nhập mã nguồn từ file",
        "type": "snippet"
    },
    {
        "label": "\\fbox{arg1}",
        "insertText": "\\fbox{${1:arg1}}",
        "detail": "Hộp đóng khung",
        "type": "snippet"
    },
    {
        "label": "\\mbox{arg1}",
        "insertText": "\\mbox{${1:arg1}}",
        "detail": "Hộp văn bản không ngắt",
        "type": "snippet"
    },
    {
        "label": "\\makebox[width][pos]arg1",
        "insertText": "\\makebox[width][pos]${1:arg1}",
        "detail": "Hộp tùy chỉnh",
        "type": "snippet"
    },
    {
        "label": "\\framebox[width][pos]arg1",
        "insertText": "\\framebox[width][pos]${1:arg1}",
        "detail": "Hộp đóng khung tùy chỉnh",
        "type": "snippet"
    },
    {
        "label": "\\parbox[pos]{width}{arg1}",
        "insertText": "\\parbox[pos]{width}{${1:arg1}}",
        "detail": "Hộp đoạn văn",
        "type": "snippet"
    },
    {
        "label": "\\raisebox{lift}[height][depth]arg1",
        "insertText": "\\raisebox{lift}[height][depth]${1:arg1}",
        "detail": "Hộp nâng cao",
        "type": "snippet"
    },
    {
        "label": "\\rule{width}{height}",
        "insertText": "\\rule{width}{height}",
        "detail": "Vẽ đường thẳng ngang",
        "type": "snippet"
    },
    {
        "label": "\\rule{0pt}{height}",
        "insertText": "\\rule{0pt}{height}",
        "detail": "Đường ngang vô hình",
        "type": "snippet"
    },
    {
        "label": "\\hspace*{len}",
        "insertText": "\\hspace*{len}",
        "detail": "Khoảng ngang bắt buộc",
        "type": "snippet"
    },
    {
        "label": "\\vspace*{len}",
        "insertText": "\\vspace*{len}",
        "detail": "Khoảng dọc bắt buộc",
        "type": "snippet"
    },
    {
        "label": "\\linebreak",
        "insertText": "\\linebreak",
        "detail": "Ngắt dòng tại vị trí",
        "type": "snippet"
    },
    {
        "label": "\\pagebreak",
        "insertText": "\\pagebreak",
        "detail": "Ngắt trang tại vị trí",
        "type": "snippet"
    },
    {
        "label": "\\nolinebreak",
        "insertText": "\\nolinebreak",
        "detail": "Không ngắt dòng",
        "type": "snippet"
    },
    {
        "label": "\\nopagebreak",
        "insertText": "\\nopagebreak",
        "detail": "Không ngắt trang",
        "type": "snippet"
    },
    {
        "label": "\\input{arg1}",
        "insertText": "\\input{${1:arg1}}",
        "detail": "Nhập file TeX",
        "type": "snippet"
    },
    {
        "label": "\\include{arg1}",
        "insertText": "\\include{${1:arg1}}",
        "detail": "Chèn file TeX (ngắt trang)",
        "type": "snippet"
    },
    {
        "label": "\\includeonly{arg1}",
        "insertText": "\\includeonly{${1:arg1}}",
        "detail": "Giới hạn file được chèn",
        "type": "snippet"
    },
    {
        "label": "\\footnote{text}",
        "insertText": "\\footnote{text}",
        "detail": "Chú thích chân trang",
        "type": "snippet"
    },
    {
        "label": "\\marginpar{text}",
        "insertText": "\\marginpar{text}",
        "detail": "Ghi chú lề trang",
        "type": "snippet"
    },
    {
        "label": "\\newcounter{name}",
        "insertText": "\\newcounter{name}",
        "detail": "Tạo bộ đếm mới",
        "type": "snippet"
    },
    {
        "label": "\\stepcounter{name}",
        "insertText": "\\stepcounter{name}",
        "detail": "Tăng bộ đếm",
        "type": "snippet"
    },
    {
        "label": "\\the\\value{name}",
        "insertText": "\\the\\value{name}",
        "detail": "In giá trị bộ đếm",
        "type": "snippet"
    },
    {
        "label": "\\bibliographystyle{style}",
        "insertText": "\\bibliographystyle{style}",
        "detail": "Kiểu BibTeX",
        "type": "snippet"
    },
    {
        "label": "\\bibliography{file}",
        "insertText": "\\bibliography{file}",
        "detail": "Nguồn tài liệu BibTeX",
        "type": "snippet"
    },
    {
        "label": "\\nocite{*}",
        "insertText": "\\nocite{*}",
        "detail": "Hiển thị không trích dẫn",
        "type": "snippet"
    },
    {
        "label": "\\citet{key}",
        "insertText": "\\citet{key}",
        "detail": "Trích dẫn dạng văn bản",
        "type": "snippet"
    },
    {
        "label": "\\citep{key}",
        "insertText": "\\citep{key}",
        "detail": "Trích dẫn trong ngoặc",
        "type": "snippet"
    },
    {
        "label": "\\citet*{key}",
        "insertText": "\\citet*{key}",
        "detail": "Trích dẫn liệt kê tác giả",
        "type": "snippet"
    },
    {
        "label": "\\citep*{key}",
        "insertText": "\\citep*{key}",
        "detail": "Trích dẫn ngoặc liệt kê",
        "type": "snippet"
    },
    {
        "label": "\\citeauthor{key}",
        "insertText": "\\citeauthor{key}",
        "detail": "Chỉ in tên tác giả",
        "type": "snippet"
    },
    {
        "label": "\\citeyear{key}",
        "insertText": "\\citeyear{key}",
        "detail": "Chỉ in năm xuất bản",
        "type": "snippet"
    },
    {
        "label": "\\setcitestyle{...}",
        "insertText": "\\setcitestyle{...}",
        "detail": "Cấu hình Natbib",
        "type": "snippet"
    },
    {
        "label": "\\bibliographystyle{plainnat}",
        "insertText": "\\bibliographystyle{plainnat}",
        "detail": "Kiểu Natbib",
        "type": "snippet"
    },
    {
        "label": "\\addbibresource{file.bib}",
        "insertText": "\\addbibresource{file.bib}",
        "detail": "Nguồn tài liệu BibLaTeX",
        "type": "snippet"
    },
    {
        "label": "\\printbibliography",
        "insertText": "\\printbibliography",
        "detail": "In danh mục tham khảo",
        "type": "snippet"
    },
    {
        "label": "\\printbibliography[title={...}]",
        "insertText": "\\printbibliography[title={...}]",
        "detail": "Đổi tiêu đề danh mục",
        "type": "snippet"
    },
    {
        "label": "\\printbibliography[type=article]",
        "insertText": "\\printbibliography[type=article]",
        "detail": "Lọc theo loại tài liệu",
        "type": "snippet"
    },
    {
        "label": "\\printbibliography[keyword={...}]",
        "insertText": "\\printbibliography[keyword={...}]",
        "detail": "Lọc theo từ khóa",
        "type": "snippet"
    },
    {
        "label": "\\printbibliography[heading=subbibintoc]",
        "insertText": "\\printbibliography[heading=subbibintoc]",
        "detail": "Chia phần danh mục",
        "type": "snippet"
    },
    {
        "label": "\\tiny",
        "insertText": "\\tiny",
        "detail": "Kích thước rất nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\scriptsize",
        "insertText": "\\scriptsize",
        "detail": "Kích thước chỉ số",
        "type": "snippet"
    },
    {
        "label": "\\footnotesize",
        "insertText": "\\footnotesize",
        "detail": "Kích thước chú thích",
        "type": "snippet"
    },
    {
        "label": "\\small",
        "insertText": "\\small",
        "detail": "Kích thước nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\normalsize",
        "insertText": "\\normalsize",
        "detail": "Kích thước thường",
        "type": "snippet"
    },
    {
        "label": "\\large",
        "insertText": "\\large",
        "detail": "Kích thước lớn",
        "type": "snippet"
    },
    {
        "label": "\\Large",
        "insertText": "\\Large",
        "detail": "Kích thước lớn hơn",
        "type": "snippet"
    },
    {
        "label": "\\LARGE",
        "insertText": "\\LARGE",
        "detail": "Kích thước rất lớn",
        "type": "snippet"
    },
    {
        "label": "\\huge",
        "insertText": "\\huge",
        "detail": "Kích thước khổng lồ",
        "type": "snippet"
    },
    {
        "label": "\\Huge",
        "insertText": "\\Huge",
        "detail": "Kích thước lớn nhất",
        "type": "snippet"
    },
    {
        "label": "\\textnormal{arg1}",
        "insertText": "\\textnormal{${1:arg1}}",
        "detail": "Chữ thường mặc định",
        "type": "snippet"
    },
    {
        "label": "\\textup{arg1}",
        "insertText": "\\textup{${1:arg1}}",
        "detail": "Chữ đứng",
        "type": "snippet"
    },
    {
        "label": "\\textsl{arg1}",
        "insertText": "\\textsl{${1:arg1}}",
        "detail": "Chữ nghiêng nhẹ",
        "type": "snippet"
    },
    {
        "label": "\\textsc{arg1}",
        "insertText": "\\textsc{${1:arg1}}",
        "detail": "Chữ in hoa nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\textmd{arg1}",
        "insertText": "\\textmd{${1:arg1}}",
        "detail": "Chữ đậm vừa",
        "type": "snippet"
    },
    {
        "label": "\\bfseries",
        "insertText": "\\bfseries",
        "detail": "Bật chế độ in đậm",
        "type": "snippet"
    },
    {
        "label": "\\itshape",
        "insertText": "\\itshape",
        "detail": "Bật chế độ in nghiêng",
        "type": "snippet"
    },
    {
        "label": "\\upshape",
        "insertText": "\\upshape",
        "detail": "Bật chế độ chữ đứng",
        "type": "snippet"
    },
    {
        "label": "\\slshape",
        "insertText": "\\slshape",
        "detail": "Bật chế độ nghiêng nhẹ",
        "type": "snippet"
    },
    {
        "label": "\\scshape",
        "insertText": "\\scshape",
        "detail": "Bật chế độ hoa nhỏ",
        "type": "snippet"
    },
    {
        "label": "\\normalfont",
        "insertText": "\\normalfont",
        "detail": "Bật chế độ bình thường",
        "type": "snippet"
    },
    {
        "label": "\\textrm{arg1}",
        "insertText": "\\textrm{${1:arg1}}",
        "detail": "Phông chữ có chân",
        "type": "snippet"
    },
    {
        "label": "\\textsf{arg1}",
        "insertText": "\\textsf{${1:arg1}}",
        "detail": "Phông chữ không chân",
        "type": "snippet"
    },
    {
        "label": "\\texttt{arg1}",
        "insertText": "\\texttt{${1:arg1}}",
        "detail": "Phông chữ máy đánh chữ",
        "type": "snippet"
    },
    {
        "label": "\\rmfamily",
        "insertText": "\\rmfamily",
        "detail": "Bật phông có chân",
        "type": "snippet"
    },
    {
        "label": "\\sffamily",
        "insertText": "\\sffamily",
        "detail": "Bật phông không chân",
        "type": "snippet"
    },
    {
        "label": "\\ttfamily",
        "insertText": "\\ttfamily",
        "detail": "Bật phông máy đánh chữ",
        "type": "snippet"
    },
    {
        "label": "\\fontsize{size}{skip}\\selectfont",
        "insertText": "\\fontsize{size}{skip}\\selectfont",
        "detail": "Kích thước phông tùy chỉnh",
        "type": "snippet"
    },
    {
        "label": "\\fontfamily{code}\\selectfont",
        "insertText": "\\fontfamily{code}\\selectfont",
        "detail": "Loại phông tùy chỉnh",
        "type": "snippet"
    },
    {
        "label": "\\fontseries{series}\\selectfont",
        "insertText": "\\fontseries{series}\\selectfont",
        "detail": "Series phông tùy chỉnh",
        "type": "snippet"
    },
    {
        "label": "\\fontshape{shape}\\selectfont",
        "insertText": "\\fontshape{shape}\\selectfont",
        "detail": "Hình dạng phông tùy chỉnh",
        "type": "snippet"
    },
    {
        "label": "\\usefont{enc}{family}{series}{shape}",
        "insertText": "\\usefont{enc}{family}{series}{shape}",
        "detail": "Đặt phông trực tiếp",
        "type": "snippet"
    },
    {
        "label": "\\setmainfont{Name}",
        "insertText": "\\setmainfont{Name}",
        "detail": "Thiết lập phông chính",
        "type": "snippet"
    },
    {
        "label": "\\setsansfont{Name}",
        "insertText": "\\setsansfont{Name}",
        "detail": "Thiết lập phông không chân",
        "type": "snippet"
    },
    {
        "label": "\\setmonofont{Name}",
        "insertText": "\\setmonofont{Name}",
        "detail": "Thiết lập phông đơn không gian",
        "type": "snippet"
    },
    {
        "label": "\\frametitle{text}",
        "insertText": "\\frametitle{text}",
        "detail": "Tiêu đề Slide",
        "type": "snippet"
    },
    {
        "label": "\\frame{\\titlepage}",
        "insertText": "\\frame{\\titlepage}",
        "detail": "Tạo trang tiêu đề",
        "type": "snippet"
    },
    {
        "label": "\\institute[options]{...}",
        "insertText": "\\institute[${1:options}]{...}",
        "detail": "Thông tin viện trường",
        "type": "snippet"
    },
    {
        "label": "\\logo{\\includegraphics{...}}",
        "insertText": "\\logo{\\includegraphics{...}}",
        "detail": "Chèn Logo",
        "type": "snippet"
    },
    {
        "label": "\\pause",
        "insertText": "\\pause",
        "detail": "Tạm dừng hiển thị",
        "type": "snippet"
    },
    {
        "label": "\\alert{text}",
        "insertText": "\\alert{text}",
        "detail": "Văn bản cảnh báo",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Madrid}",
        "insertText": "\\usetheme{Madrid}",
        "detail": "Chọn chủ đề giao diện",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{beaver}",
        "insertText": "\\usecolortheme{beaver}",
        "detail": "Chọn chủ đề màu sắc",
        "type": "snippet"
    },
    {
        "label": "\\usefonttheme{serif}",
        "insertText": "\\usefonttheme{serif}",
        "detail": "Chọn chủ đề phông chữ",
        "type": "snippet"
    },
    {
        "label": "\\column{0.5\\textwidth}",
        "insertText": "\\column{0.5\\textwidth}",
        "detail": "Cột đơn",
        "type": "snippet"
    },
    {
        "label": "\\AtBeginSection[options]arg2",
        "insertText": "\\AtBeginSection[${1:options}]${2:arg2}",
        "detail": "Cấu hình hiển thị mục lục",
        "type": "snippet"
    },
    {
        "label": "\\pdsetup{trans=Split}",
        "insertText": "\\pdsetup{trans=Split}",
        "detail": "Hiệu ứng chuyển trang",
        "type": "snippet"
    },
    {
        "label": "\\pdsetup{palette=...}",
        "insertText": "\\pdsetup{palette=...}",
        "detail": "Bảng màu Powerdot",
        "type": "snippet"
    },
    {
        "label": "\\block{Title}{Text}",
        "insertText": "\\block{Title}{Text}",
        "detail": "Hộp postr",
        "type": "snippet"
    },
    {
        "label": "\\column{0.5}",
        "insertText": "\\column{0.5}",
        "detail": "Cột đơn postr",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Board}",
        "insertText": "\\usetheme{Board}",
        "detail": "Chủ đề giao diện postr",
        "type": "snippet"
    },
    {
        "label": "\\note[options]{Text}",
        "insertText": "\\note[${1:options}]{Text}",
        "detail": "Ghi chú nổi postr",
        "type": "snippet"
    },
    {
        "label": "\\newcommand{\\\\command}[args]{definition}",
        "insertText": "\\newcommand{\\\\${1:command}}[${2:args}]{${3:definition}}",
        "detail": "Định nghĩa lệnh mới",
        "type": "snippet"
    },
    {
        "label": "\\providecommand{\\cmd}{def}",
        "insertText": "\\providecommand{\\cmd}{def}",
        "detail": "Cung cấp lệnh",
        "type": "snippet"
    },
    {
        "label": "\\show\\cmd",
        "insertText": "\\show\\cmd",
        "detail": "Hiển thị định nghĩa lệnh",
        "type": "snippet"
    },
    {
        "label": "\\newenvironment{name}[args]{begindef}{enddef}",
        "insertText": "\\newenvironment{${1:name}}[${2:args}]{${3:begindef}}{${4:enddef}}",
        "detail": "Tạo môi trường mới",
        "type": "snippet"
    },
    {
        "label": "\\renewenvironment{name}{beg}{end}",
        "insertText": "\\renewenvironment{name}{beg}{end}",
        "detail": "Định nghĩa lại môi trường",
        "type": "snippet"
    },
    {
        "label": "\\newcounter{ctr}",
        "insertText": "\\newcounter{ctr}",
        "detail": "Tạo bộ đếm mới",
        "type": "snippet"
    },
    {
        "label": "\\newcounter{ctr}[parent]",
        "insertText": "\\newcounter{ctr}[parent]",
        "detail": "Tạo bộ đếm phụ thuộc",
        "type": "snippet"
    },
    {
        "label": "\\stepcounter{ctr}",
        "insertText": "\\stepcounter{ctr}",
        "detail": "Tăng giá trị bộ đếm",
        "type": "snippet"
    },
    {
        "label": "\\refstepcounter{ctr}",
        "insertText": "\\refstepcounter{ctr}",
        "detail": "Tăng bộ đếm và tham chiếu",
        "type": "snippet"
    },
    {
        "label": "\\addtocounter{ctr}{val}",
        "insertText": "\\addtocounter{ctr}{val}",
        "detail": "Cộng thêm vào bộ đếm",
        "type": "snippet"
    },
    {
        "label": "\\value{ctr}",
        "insertText": "\\value{ctr}",
        "detail": "Lấy giá trị bộ đếm",
        "type": "snippet"
    },
    {
        "label": "\\arabic{ctr}",
        "insertText": "\\arabic{ctr}",
        "detail": "Hiển thị số Ả Rập",
        "type": "snippet"
    },
    {
        "label": "\\roman{ctr}",
        "insertText": "\\roman{ctr}",
        "detail": "Hiển thị số La Mã thường",
        "type": "snippet"
    },
    {
        "label": "\\Roman{ctr}",
        "insertText": "\\Roman{ctr}",
        "detail": "Hiển thị số La Mã hoa",
        "type": "snippet"
    },
    {
        "label": "\\alph{ctr}",
        "insertText": "\\alph{ctr}",
        "detail": "Hiển thị chữ cái thường",
        "type": "snippet"
    },
    {
        "label": "\\Alph{ctr}",
        "insertText": "\\Alph{ctr}",
        "detail": "Hiển thị chữ cái hoa",
        "type": "snippet"
    },
    {
        "label": "\\fnsymbol{ctr}",
        "insertText": "\\fnsymbol{ctr}",
        "detail": "Hiển thị ký hiệu chú thích",
        "type": "snippet"
    },
    {
        "label": "\\newtheorem{name}{print}",
        "insertText": "\\newtheorem{${1:name}}{${2:print}}",
        "detail": "Định nghĩa định lý mới",
        "type": "snippet"
    },
    {
        "label": "\\theoremstyle{style}",
        "insertText": "\\theoremstyle{style}",
        "detail": "Kiểu dáng định lý",
        "type": "snippet"
    },
    {
        "label": "\\qedsymbol",
        "insertText": "\\qedsymbol",
        "detail": "Ký hiệu kết thúc chứng minh",
        "type": "snippet"
    },
    {
        "label": "\\newlength{\\len}",
        "insertText": "\\newlength{\\len}",
        "detail": "Tạo độ dài mới",
        "type": "snippet"
    },
    {
        "label": "\\AtEndDocument{arg1}",
        "insertText": "\\AtEndDocument{${1:arg1}}",
        "detail": "Hành động sau văn bản",
        "type": "snippet"
    },
    {
        "label": "\\urlstyle{rm}",
        "insertText": "\\urlstyle{rm}",
        "detail": "Thiết lập phông URL",
        "type": "snippet"
    },
    {
        "label": "\\leftmark",
        "insertText": "\\leftmark",
        "detail": "Tiêu đề trang hiện tại",
        "type": "snippet"
    },
    {
        "label": "\\rightmark",
        "insertText": "\\rightmark",
        "detail": "Tiêu đề tiết hiện tại",
        "type": "snippet"
    },
    {
        "label": "\\setdefaultlanguage{arg1}",
        "insertText": "\\setdefaultlanguage{${1:arg1}}",
        "detail": "Thiết lập ngôn ngữ chính",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguages{arg1}",
        "insertText": "\\setotherlanguages{${1:arg1}}",
        "detail": "Thiết lập ngôn ngữ phụ",
        "type": "snippet"
    },
    {
        "label": "\\selectlanguage{arg1}",
        "insertText": "\\selectlanguage{${1:arg1}}",
        "detail": "Chọn ngôn ngữ",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{lang}{text}",
        "insertText": "\\foreignlanguage{lang}{text}",
        "detail": "Đoạn ngôn ngữ khác",
        "type": "snippet"
    },
    {
        "label": "\\babelprovide[import]{lang}",
        "insertText": "\\babelprovide[import]{lang}",
        "detail": "Khai báo thêm ngôn ngữ",
        "type": "snippet"
    },
    {
        "label": "\\babelfont{rm}{font}",
        "insertText": "\\babelfont{rm}{font}",
        "detail": "Thiết lập phông chữ ngôn ngữ",
        "type": "snippet"
    },
    {
        "label": "\\setCJKmainfont{arg1}",
        "insertText": "\\setCJKmainfont{${1:arg1}}",
        "detail": "Thiết lập phông CJK chính",
        "type": "snippet"
    },
    {
        "label": "\\setCJKsansfont{arg1}",
        "insertText": "\\setCJKsansfont{${1:arg1}}",
        "detail": "Thiết lập phông CJK không chân",
        "type": "snippet"
    },
    {
        "label": "\\setCJKmonofont{arg1}",
        "insertText": "\\setCJKmonofont{${1:arg1}}",
        "detail": "Thiết lập phông CJK đơn không gian",
        "type": "snippet"
    },
    {
        "label": "\\nombre{arg1}",
        "insertText": "\\nombre{${1:arg1}}",
        "detail": "In số kiểu Pháp",
        "type": "snippet"
    },
    {
        "label": "\\newfontfamily\\cyrillicfont{arg1}",
        "insertText": "\\newfontfamily\\cyrillicfont{${1:arg1}}",
        "detail": "Thiết lập phông Cyrillic",
        "type": "snippet"
    },
    {
        "label": "\\textLR{arg1}",
        "insertText": "\\textLR{${1:arg1}}",
        "detail": "Chèn chữ Latin",
        "type": "snippet"
    },
    {
        "label": "\\hyphenation{arg1}",
        "insertText": "\\hyphenation{${1:arg1}}",
        "detail": "Quy tắc ngắt dòng",
        "type": "snippet"
    },
    {
        "label": "\\nobreak",
        "insertText": "\\nobreak",
        "detail": "Ngăn ngắt dòng",
        "type": "snippet"
    },
    {
        "label": "\\textquote{arg1}",
        "insertText": "\\textquote{${1:arg1}}",
        "detail": "Trích dẫn trong dòng",
        "type": "snippet"
    },
    {
        "label": "\\say{arg1}",
        "insertText": "\\say{${1:arg1}}",
        "detail": "Lệnh trích dẫn",
        "type": "snippet"
    },
    {
        "label": "\\draw (x1,y1) to(x2,y2);",
        "insertText": "\\draw (x1,y1) to(x2,y2);",
        "detail": "Lệnh vẽ dây nối",
        "type": "snippet"
    },
    {
        "label": "\\feynmandiagram[opt]{...}",
        "insertText": "\\feynmandiagram[opt]{...}",
        "detail": "Vẽ biểu đồ Feynman nhanh",
        "type": "snippet"
    },
    {
        "label": "\\vertex",
        "insertText": "\\vertex",
        "detail": "Định nghĩa đỉnh",
        "type": "snippet"
    },
    {
        "label": "\\diagram*",
        "insertText": "\\diagram*",
        "detail": "Khai báo sơ đồ",
        "type": "snippet"
    },
    {
        "label": "\\chemfig{arg1}",
        "insertText": "\\chemfig{${1:arg1}}",
        "detail": "Lệnh vẽ phân tử",
        "type": "snippet"
    },
    {
        "label": "\\ce{arg1}",
        "insertText": "\\ce{${1:arg1}}",
        "detail": "Viết công thức hóa học",
        "type": "snippet"
    },
    {
        "label": "\\ce{->}",
        "insertText": "\\ce{->}",
        "detail": "Mũi tên phản ứng",
        "type": "snippet"
    },
    {
        "label": "\\ce{<=>}",
        "insertText": "\\ce{<=>}",
        "detail": "Mũi tên thuận nghịch",
        "type": "snippet"
    },
    {
        "label": "\\ce{^}",
        "insertText": "\\ce{^}",
        "detail": "Trạng thái bay hơi",
        "type": "snippet"
    },
    {
        "label": "\\atom{pos}{spec}",
        "insertText": "\\atom{pos}{spec}",
        "detail": "Cấu hình nguyên tử",
        "type": "snippet"
    },
    {
        "label": "\\molecule{spec}",
        "insertText": "\\molecule{spec}",
        "detail": "Cấu hình phân tử",
        "type": "snippet"
    },
    {
        "label": "\\charge{val}{elem}",
        "insertText": "\\charge{val}{elem}",
        "detail": "Khai báo hóa trị",
        "type": "snippet"
    },
    {
        "label": "\\ce{<->}",
        "insertText": "\\ce{<->}",
        "detail": "Mũi tên phản ứng cân bằng",
        "type": "snippet"
    },
    {
        "label": "\\ce{+}",
        "insertText": "\\ce{+}",
        "detail": "Mũi tên phản ứng cộng",
        "type": "snippet"
    },
    {
        "label": "\\tcbox{arg1}",
        "insertText": "\\tcbox{${1:arg1}}",
        "detail": "Hộp màu sắc đơn giản",
        "type": "snippet"
    },
    {
        "label": "\\State",
        "insertText": "\\State",
        "detail": "Dòng lệnh thuật toán",
        "type": "snippet"
    },
    {
        "label": "\\If{arg1}",
        "insertText": "\\If{${1:arg1}}",
        "detail": "Vòng lặp Nếu",
        "type": "snippet"
    },
    {
        "label": "\\For{arg1}",
        "insertText": "\\For{${1:arg1}}",
        "detail": "Vòng lặp Cho",
        "type": "snippet"
    },
    {
        "label": "\\While{arg1}",
        "insertText": "\\While{${1:arg1}}",
        "detail": "Vòng lặp Trong khi",
        "type": "snippet"
    },
    {
        "label": "\\Return",
        "insertText": "\\Return",
        "detail": "Trả về giá trị",
        "type": "snippet"
    },
    {
        "label": "\\pgfplotsset{compat=1.9}",
        "insertText": "\\pgfplotsset{compat=1.9}",
        "detail": "Cấu hình phiên bản Pgf",
        "type": "snippet"
    },
    {
        "label": "\\addplot[opt]{func};",
        "insertText": "\\addplot[opt]{func};",
        "detail": "Vẽ đồ thị 2D",
        "type": "snippet"
    },
    {
        "label": "\\addplot3[opt]{func};",
        "insertText": "\\addplot3[opt]{func};",
        "detail": "Vẽ đồ thị 3D",
        "type": "snippet"
    },
    {
        "label": "\\addlegendentry{text}",
        "insertText": "\\addlegendentry{text}",
        "detail": "Thêm chú giải",
        "type": "snippet"
    },
    {
        "label": "\\question[points]",
        "insertText": "\\question[points]",
        "detail": "Tạo câu hỏi mới",
        "type": "snippet"
    },
    {
        "label": "\\choice",
        "insertText": "\\choice",
        "detail": "Lựa chọn đáp án",
        "type": "snippet"
    },
    {
        "label": "\\CorrectChoice",
        "insertText": "\\CorrectChoice",
        "detail": "Đáp án đúng",
        "type": "snippet"
    },
    {
        "label": "\\gradetable[h][questions]",
        "insertText": "\\gradetable[h][questions]",
        "detail": "Bảng điểm tổng hợp",
        "type": "snippet"
    },
    {
        "label": "\\pointsinmargin",
        "insertText": "\\pointsinmargin",
        "detail": "Điểm số lề trang",
        "type": "snippet"
    },
    {
        "label": "\\newchessgame",
        "insertText": "\\newchessgame",
        "detail": "Khởi tạo ván cờ",
        "type": "snippet"
    },
    {
        "label": "\\mainline{1. e4 e5}",
        "insertText": "\\mainline{1. e4 e5}",
        "detail": "Ghi nước đi",
        "type": "snippet"
    },
    {
        "label": "\\chessboard",
        "insertText": "\\chessboard",
        "detail": "Hiển thị bàn cờ",
        "type": "snippet"
    },
    {
        "label": "\\lastmove",
        "insertText": "\\lastmove",
        "detail": "Hiển thị nước cuối",
        "type": "snippet"
    },
    {
        "label": "\\chessboard[setfen=...]",
        "insertText": "\\chessboard[setfen=...]",
        "detail": "Thiết lập thế cờ FEN",
        "type": "snippet"
    },
    {
        "label": "\\diagram{arg1}",
        "insertText": "\\diagram{${1:arg1}}",
        "detail": "Sơ đồ đan len",
        "type": "snippet"
    },
    {
        "label": "\\note{col1}{col2}{title}{text}",
        "insertText": "\\note{col1}{col2}{title}{text}",
        "detail": "Hộp ghi chú đan",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{circuits.logic.US}",
        "insertText": "\\usetikzlibrary{circuits.logic.US}",
        "detail": "Thư viện cổng logic",
        "type": "snippet"
    },
    {
        "label": "\\ex",
        "insertText": "\\ex",
        "detail": "Mục ví dụ số",
        "type": "snippet"
    },
    {
        "label": "\\sn",
        "insertText": "\\sn",
        "detail": "wallet.dụ phụ",
        "type": "snippet"
    },
    {
        "label": "\\glll",
        "insertText": "\\glll",
        "detail": "Dòng chú thích từ ngữ",
        "type": "snippet"
    },
    {
        "label": "\\cref{arg1}",
        "insertText": "\\cref{${1:arg1}}",
        "detail": "Trích dẫn thông minh (thường)",
        "type": "snippet"
    },
    {
        "label": "\\Cref{arg1}",
        "insertText": "\\Cref{${1:arg1}}",
        "detail": "Trích dẫn thông minh (hoa)",
        "type": "snippet"
    },
    {
        "label": "\\cref{label1,label2}",
        "insertText": "\\cref{label1,label2}",
        "detail": "Trích dẫn nhiều nhãn",
        "type": "snippet"
    },
    {
        "label": "\\crefrange{start}{end}",
        "insertText": "\\crefrange{start}{end}",
        "detail": "Trích dẫn dải nhãn",
        "type": "snippet"
    },
    {
        "label": "\\Crefrange{start}{end}",
        "insertText": "\\Crefrange{start}{end}",
        "detail": "Trích dẫn dải nhãn (hoa)",
        "type": "snippet"
    },
    {
        "label": "\\cpageref{arg1}",
        "insertText": "\\cpageref{${1:arg1}}",
        "detail": "Trích dẫn trang tham chiếu",
        "type": "snippet"
    },
    {
        "label": "\\Cpageref{arg1}",
        "insertText": "\\Cpageref{${1:arg1}}",
        "detail": "Trích dẫn trang (hoa)",
        "type": "snippet"
    },
    {
        "label": "\\crefname{type}{singular}{plural}",
        "insertText": "\\crefname{type}{singular}{plural}",
        "detail": "Định nghĩa tên trích dẫn",
        "type": "snippet"
    },
    {
        "label": "\\vref{arg1}",
        "insertText": "\\vref{${1:arg1}}",
        "detail": "Tham chiếu kèm trang",
        "type": "snippet"
    },
    {
        "label": "\\Vref{arg1}",
        "insertText": "\\Vref{${1:arg1}}",
        "detail": "Tham chiếu trang viết hoa",
        "type": "snippet"
    },
    {
        "label": "\\namecref{arg1}",
        "insertText": "\\namecref{${1:arg1}}",
        "detail": "Trích dẫn bằng tên",
        "type": "snippet"
    },
    {
        "label": "\\nameCref{arg1}",
        "insertText": "\\nameCref{${1:arg1}}",
        "detail": "Trích dẫn bằng tên hoa",
        "type": "snippet"
    },
    {
        "label": "\\labelcref{arg1}",
        "insertText": "\\labelcref{${1:arg1}}",
        "detail": "Chỉ trích dẫn nhãn kiểu cref",
        "type": "snippet"
    },
    {
        "label": "\\todo{arg1}",
        "insertText": "\\todo{${1:arg1}}",
        "detail": "Ghi chú lề",
        "type": "snippet"
    },
    {
        "label": "\\todo[color=green]arg1",
        "insertText": "\\todo[color=green]${1:arg1}",
        "detail": "Ghi chú lề (màu)",
        "type": "snippet"
    },
    {
        "label": "\\todo[inline]arg1",
        "insertText": "\\todo[inline]${1:arg1}",
        "detail": "Ghi chú trực tiếp trong dòng",
        "type": "snippet"
    },
    {
        "label": "\\listoftodos",
        "insertText": "\\listoftodos",
        "detail": "Danh sách ghi chú",
        "type": "snippet"
    },
    {
        "label": "\\missingfigure{arg1}",
        "insertText": "\\missingfigure{${1:arg1}}",
        "detail": "Đánh dấu thiếu hình vẽ",
        "type": "snippet"
    },
    {
        "label": "\\todo[author=Name]arg1",
        "insertText": "\\todo[author=Name]${1:arg1}",
        "detail": "Gắn nhãn tác giả ghi chú",
        "type": "snippet"
    },
    {
        "label": "\\added{arg1}",
        "insertText": "\\added{${1:arg1}}",
        "detail": "Đánh dấu thêm mới",
        "type": "snippet"
    },
    {
        "label": "\\added[id=id, remark=Ghi chú]arg1",
        "insertText": "\\added[id=id, remark=Ghi chú]${1:arg1}",
        "detail": "Thêm mới có ghi chú",
        "type": "snippet"
    },
    {
        "label": "\\deleted{arg1}",
        "insertText": "\\deleted{${1:arg1}}",
        "detail": "Đánh dấu xóa đi",
        "type": "snippet"
    },
    {
        "label": "\\replaced{new}{old}",
        "insertText": "\\replaced{new}{old}",
        "detail": "Đánh dấu thay thế",
        "type": "snippet"
    },
    {
        "label": "\\highlight{arg1}",
        "insertText": "\\highlight{${1:arg1}}",
        "detail": "Đánh dấu làm nổi bật",
        "type": "snippet"
    },
    {
        "label": "\\listofchanges",
        "insertText": "\\listofchanges",
        "detail": "Danh sách thay đổi",
        "type": "snippet"
    },
    {
        "label": "\\tcbsubtitle{arg1}",
        "insertText": "\\tcbsubtitle{${1:arg1}}",
        "detail": "Tcolorbox hai phần",
        "type": "snippet"
    },
    {
        "label": "\\tcblower",
        "insertText": "\\tcblower",
        "detail": "Chia nửa hộp màu",
        "type": "snippet"
    },
    {
        "label": "\\newtcbtheorem{mytheo}{Định lý}{colback=green!5,colframe=green!35!none}{th}",
        "insertText": "\\newtcbtheorem{mytheo}{Định lý}{colback=green!5,colframe=green!35!none}{th}",
        "detail": "Định nghĩa định lý tcolorbox",
        "type": "snippet"
    },
    {
        "label": "\\arrow[l]",
        "insertText": "\\arrow[l]",
        "detail": "Mũi tên sang trái tikz-cd",
        "type": "snippet"
    },
    {
        "label": "\\arrow[u]",
        "insertText": "\\arrow[u]",
        "detail": "Mũi tên lên trên tikz-cd",
        "type": "snippet"
    },
    {
        "label": "\\arrow[d]",
        "insertText": "\\arrow[d]",
        "detail": "Mũi tên xuống dưới tikz-cd",
        "type": "snippet"
    },
    {
        "label": "\\arrow[ru]",
        "insertText": "\\arrow[ru]",
        "detail": "Mũi tên chéo lên phải tikz-cd",
        "type": "snippet"
    },
    {
        "label": "\\arrow[ld]",
        "insertText": "\\arrow[ld]",
        "detail": "Mũi tên chéo xuống trái tikz-cd",
        "type": "snippet"
    },
    {
        "label": "\\arrow[r, dash]",
        "insertText": "\\arrow[r, dash]",
        "detail": "Mũi tên hai chiều vô hướng",
        "type": "snippet"
    },
    {
        "label": "\\arrow[r, leftrightarrow]",
        "insertText": "\\arrow[r, leftrightarrow]",
        "detail": "Mũi tên hai chiều có hướng",
        "type": "snippet"
    },
    {
        "label": "\\arrow[r, hook]",
        "insertText": "\\arrow[r, hook]",
        "detail": "Mũi tên móc hook",
        "type": "snippet"
    },
    {
        "label": "\\arrow[r, maps to]",
        "insertText": "\\arrow[r, maps to]",
        "detail": "Mũi tên ánh xạ maps to",
        "type": "snippet"
    },
    {
        "label": "\\arrow[r, dashed]",
        "insertText": "\\arrow[r, dashed]",
        "detail": "Mũi tên đứt nét dashed",
        "type": "snippet"
    },
    {
        "label": "\\arrow[r, \"f\"]",
        "insertText": "\\arrow[r, \"f\"]",
        "detail": "Ghi chú trên mũi tên tikz-cd",
        "type": "snippet"
    },
    {
        "label": "\\arrow[r, \"f\"']",
        "insertText": "\\arrow[r, \"f\"']",
        "detail": "Ghi chú dưới mũi tên tikz-cd",
        "type": "snippet"
    },
    {
        "label": "\\arrow[loop above]",
        "insertText": "\\arrow[loop above]",
        "detail": "Tạo vòng lặp loop tikz-cd",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{automata,positioning}",
        "insertText": "\\usetikzlibrary{automata,positioning}",
        "detail": "Thư viện TikZ Automata",
        "type": "snippet"
    },
    {
        "label": "\\node(q_0) {$q_0$};",
        "insertText": "\\node(q_0) {$q_0$};",
        "detail": "Trạng thái khởi tạo Automata",
        "type": "snippet"
    },
    {
        "label": "\\node(q_1) {$q_1$};",
        "insertText": "\\node(q_1) {$q_1$};",
        "detail": "Trạng thái bình thường Automata",
        "type": "snippet"
    },
    {
        "label": "\\node(q_2) {$q_2$};",
        "insertText": "\\node(q_2) {$q_2$};",
        "detail": "Trạng thái kết thúc Automata",
        "type": "snippet"
    },
    {
        "label": "\\path(q_0) edge node {0} (q_1);",
        "insertText": "\\path(q_0) edge node {0} (q_1);",
        "detail": "Đường đi Transition thẳng",
        "type": "snippet"
    },
    {
        "label": "\\path(q_1) edge node {1} ();",
        "insertText": "\\path(q_1) edge node {1} ();",
        "detail": "Đường đi vòng Loop Automata",
        "type": "snippet"
    },
    {
        "label": "\\path(q_1) edge node {0} (q_2);",
        "insertText": "\\path(q_1) edge node {0} (q_2);",
        "detail": "Đường đi cong Automata",
        "type": "snippet"
    },
    {
        "label": "\\Tree",
        "insertText": "\\Tree",
        "detail": "Môi trường Tikz-qtree",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{mindmap}",
        "insertText": "\\usetikzlibrary{mindmap}",
        "detail": "Thư viện Mindmap TikZ",
        "type": "snippet"
    },
    {
        "label": "\\node{Root}",
        "insertText": "\\node{Root}",
        "detail": "Gốc sơ đồ gốc",
        "type": "snippet"
    },
    {
        "label": "\\gantttitle{title}{slots}",
        "insertText": "\\gantttitle{${1:title}}{${2:slots}}",
        "detail": "Thanh tiêu đề thời gian Gantt",
        "type": "snippet"
    },
    {
        "label": "\\gantttitlelist{start,...,end}{slots}",
        "insertText": "\\gantttitlelist{${1:start},...,${2:end}}{${3:slots}}",
        "detail": "Dải thời gian Gantt",
        "type": "snippet"
    },
    {
        "label": "\\ganttbar{task}{start}{end}",
        "insertText": "\\ganttbar{${1:task}}{${2:start}}{${3:end}}",
        "detail": "Thanh nhiệm vụ Gantt",
        "type": "snippet"
    },
    {
        "label": "\\ganttgroup{group_name}{start}{end}",
        "insertText": "\\ganttgroup{${1:group_name}}{${2:start}}{${3:end}}",
        "detail": "Hoạt động nhóm Gantt",
        "type": "snippet"
    },
    {
        "label": "\\ganttmilestone{milestone_name}{slot}",
        "insertText": "\\ganttmilestone{${1:milestone_name}}{${2:slot}}",
        "detail": "Cột mốc Gantt",
        "type": "snippet"
    },
    {
        "label": "\\ganttlink{elem0}{elem1}",
        "insertText": "\\ganttlink{${1:elem0}}{${2:elem1}}",
        "detail": "Kết nối nhiệm vụ Gantt",
        "type": "snippet"
    },
    {
        "label": "\\moderncvstyle{classic}",
        "insertText": "\\moderncvstyle{classic}",
        "detail": "Chủ đề Moderncv Classic",
        "type": "snippet"
    },
    {
        "label": "\\moderncvstyle{casual}",
        "insertText": "\\moderncvstyle{casual}",
        "detail": "Chủ đề Moderncv Casual",
        "type": "snippet"
    },
    {
        "label": "\\moderncvstyle{banking}",
        "insertText": "\\moderncvstyle{banking}",
        "detail": "Chủ đề Moderncv Banking",
        "type": "snippet"
    },
    {
        "label": "\\moderncvcolor{blue}",
        "insertText": "\\moderncvcolor{blue}",
        "detail": "Màu sắc Moderncv",
        "type": "snippet"
    },
    {
        "label": "\\name{John}{Doe}",
        "insertText": "\\name{John}{Doe}",
        "detail": "Thông tin Tên CV",
        "type": "snippet"
    },
    {
        "label": "\\photo[64pt][0.4pt]{picture.jpg}",
        "insertText": "\\photo[64pt][0.4pt]{picture.jpg}",
        "detail": "Chèn ảnh thẻ CV",
        "type": "snippet"
    },
    {
        "label": "\\makecvtitle",
        "insertText": "\\makecvtitle",
        "detail": "Tạo tiêu đề CV",
        "type": "snippet"
    },
    {
        "label": "\\cventry{Năm}{Bằng cấp}{Trường}{Thành phố}{Hạng}{Mô tả}",
        "insertText": "\\cventry{Năm}{Bằng cấp}{Trường}{Thành phố}{Hạng}{Mô tả}",
        "detail": "Mô tả chi tiết CV",
        "type": "snippet"
    },
    {
        "label": "\\cvitemwithcomment{Ngôn ngữ 1}{Mức độ}{Bình luận}",
        "insertText": "\\cvitemwithcomment{Ngôn ngữ 1}{Mức độ}{Bình luận}",
        "detail": "Mục thông tin thêm CV",
        "type": "snippet"
    },
    {
        "label": "\\cvlistdoubleitem{Item 1}{Item 2}",
        "insertText": "\\cvlistdoubleitem{Item 1}{Item 2}",
        "detail": "Danh sách CV đôi",
        "type": "snippet"
    },
    {
        "label": "\\lstset{basicstyle=\\ttfamily, keywordstyle=\\bfseries, breaklines=true}",
        "insertText": "\\lstset{basicstyle=\\ttfamily, keywordstyle=\\bfseries, breaklines=true}",
        "detail": "Thiết lập mã nguồn Listings",
        "type": "snippet"
    },
    {
        "label": "\\lstset{numbers=left, numberstyle=\\tiny, stepnumber=1}",
        "insertText": "\\lstset{numbers=left, numberstyle=\\tiny, stepnumber=1}",
        "detail": "Hiển thị số dòng Listings",
        "type": "snippet"
    },
    {
        "label": "\\lstset{keywordstyle=\\color{blue}, stringstyle=\\color{red}}",
        "insertText": "\\lstset{keywordstyle=\\color{blue}, stringstyle=\\color{red}}",
        "detail": "Màu sắc mã nguồn Listings",
        "type": "snippet"
    },
    {
        "label": "\\mintinline{python}{logger.info(\"Code\")}",
        "insertText": "\\mintinline{python}{logger.info(\"Code\")}",
        "detail": "Lệnh nội dòng Minted",
        "type": "snippet"
    },
    {
        "label": "\\lettrine{T}{rong} quá khứ",
        "insertText": "\\lettrine{T}{rong} quá khứ",
        "detail": "Chèn chữ to đầu đoạn",
        "type": "snippet"
    },
    {
        "label": "\\epigraph{\"Quote\"}{\\textit{Tác giả}}",
        "insertText": "\\epigraph{\"Quote\"}{\\textit{Tác giả}}",
        "detail": "Chèn trích dẫn đầu chương",
        "type": "snippet"
    },
    {
        "label": "\\SetWatermarkText{BẢN NHÁP}",
        "insertText": "\\SetWatermarkText{BẢN NHÁP}",
        "detail": "Thiết lập chữ Watermark",
        "type": "snippet"
    },
    {
        "label": "\\chemfig{*5(-=-=-)}",
        "insertText": "\\chemfig{*5(-=-=-)}",
        "detail": "Vòng đa giác hóa học Chemfig",
        "type": "snippet"
    },
    {
        "label": "\\ce{A ->B}",
        "insertText": "\\ce{A ->B}",
        "detail": "Phản ứng xúc tác trên mũi tên",
        "type": "snippet"
    },
    {
        "label": "\\sORB",
        "insertText": "\\sORB",
        "detail": "Tạo Orbital s Modiagram",
        "type": "snippet"
    },
    {
        "label": "\\pORB",
        "insertText": "\\pORB",
        "detail": "Tạo Orbital p Modiagram",
        "type": "snippet"
    },
    {
        "label": "\\tdplotsetmaincoords{70}{110}",
        "insertText": "\\tdplotsetmaincoords{70}{110}",
        "detail": "Góc nhìn 3D",
        "type": "snippet"
    },
    {
        "label": "\\draw(0,0,0) -- (1,0,0) node[anchor=north east]{$x$};",
        "insertText": "\\draw(0,0,0) -- (1,0,0) node[anchor=north east]{$x$};",
        "detail": "Trục Ox 3D",
        "type": "snippet"
    },
    {
        "label": "\\draw(0,0,0) -- (0,1,0) node[anchor=north west]{$y$};",
        "insertText": "\\draw(0,0,0) -- (0,1,0) node[anchor=north west]{$y$};",
        "detail": "Trục Oy 3D",
        "type": "snippet"
    },
    {
        "label": "\\draw(0,0,0) -- (0,0,1) node[anchor=south]{$z$};",
        "insertText": "\\draw(0,0,0) -- (0,0,1) node[anchor=south]{$z$};",
        "detail": "Trục Oz 3D",
        "type": "snippet"
    },
    {
        "label": "\\toprule[1.5pt]",
        "insertText": "\\toprule[1.5pt]",
        "detail": "Kẻ dòng trên cùng tiêu chuẩn",
        "type": "snippet"
    },
    {
        "label": "\\midrule[1pt]",
        "insertText": "\\midrule[1pt]",
        "detail": "Kẻ dòng giữa tiêu chuẩn",
        "type": "snippet"
    },
    {
        "label": "\\bottomrule[1.5pt]",
        "insertText": "\\bottomrule[1.5pt]",
        "detail": "Kẻ dòng đáy tiêu chuẩn",
        "type": "snippet"
    },
    {
        "label": "\\multicolumn{2}{c}{Title}",
        "insertText": "\\multicolumn{2}{c}{Title}",
        "detail": "Gộp cột và căn giữa bảng",
        "type": "snippet"
    },
    {
        "label": "\\multirow{3}{*}{Title}",
        "insertText": "\\multirow{3}{*}{Title}",
        "detail": "Gộp dòng tự động bảng",
        "type": "snippet"
    },
    {
        "label": "\\titleformat{\\chapter}[display]{\\normalfont\\huge\\bfseries}{\\chaptertitlename\\ \\thechapter}{20pt}{\\Huge}",
        "insertText": "\\titleformat{\\chapter}[display]{\\normalfont\\huge\\bfseries}{\\chaptertitlename\\ \\thechapter}{20pt}{\\Huge}",
        "detail": "Tùy chỉnh định dạng Chapter",
        "type": "snippet"
    },
    {
        "label": "\\titleformat{\\section}{\\normalfont\\Large\\bfseries}{\\thesection}{1em}{arg1}",
        "insertText": "\\titleformat{\\section}{\\normalfont\\Large\\bfseries}{\\thesection}{1em}{${1:arg1}}",
        "detail": "Tùy chỉnh định dạng Section",
        "type": "snippet"
    },
    {
        "label": "\\fillwithlines{1in}",
        "insertText": "\\fillwithlines{1in}",
        "detail": "Gạch chấm chấm điền đáp án",
        "type": "snippet"
    },
    {
        "label": "\\varpi",
        "insertText": "\\varpi",
        "detail": "Ký tự Hy Lạp varpi",
        "type": "snippet"
    },
    {
        "label": "\\varsigma",
        "insertText": "\\varsigma",
        "detail": "Ký tự Hy Lạp varsigma",
        "type": "snippet"
    },
    {
        "label": "\\color{black}",
        "insertText": "\\color{black}",
        "detail": "Màu chữ black",
        "type": "snippet"
    },
    {
        "label": "\\color{blue}",
        "insertText": "\\color{blue}",
        "detail": "Màu chữ blue",
        "type": "snippet"
    },
    {
        "label": "\\color{brown}",
        "insertText": "\\color{brown}",
        "detail": "Màu chữ brown",
        "type": "snippet"
    },
    {
        "label": "\\color{cyan}",
        "insertText": "\\color{cyan}",
        "detail": "Màu chữ cyan",
        "type": "snippet"
    },
    {
        "label": "\\color{darkgray}",
        "insertText": "\\color{darkgray}",
        "detail": "Màu chữ darkgray",
        "type": "snippet"
    },
    {
        "label": "\\color{gray}",
        "insertText": "\\color{gray}",
        "detail": "Màu chữ gray",
        "type": "snippet"
    },
    {
        "label": "\\color{green}",
        "insertText": "\\color{green}",
        "detail": "Màu chữ green",
        "type": "snippet"
    },
    {
        "label": "\\color{lightgray}",
        "insertText": "\\color{lightgray}",
        "detail": "Màu chữ lightgray",
        "type": "snippet"
    },
    {
        "label": "\\color{lime}",
        "insertText": "\\color{lime}",
        "detail": "Màu chữ lime",
        "type": "snippet"
    },
    {
        "label": "\\color{magenta}",
        "insertText": "\\color{magenta}",
        "detail": "Màu chữ magenta",
        "type": "snippet"
    },
    {
        "label": "\\color{olive}",
        "insertText": "\\color{olive}",
        "detail": "Màu chữ olive",
        "type": "snippet"
    },
    {
        "label": "\\color{orange}",
        "insertText": "\\color{orange}",
        "detail": "Màu chữ orange",
        "type": "snippet"
    },
    {
        "label": "\\color{pink}",
        "insertText": "\\color{pink}",
        "detail": "Màu chữ pink",
        "type": "snippet"
    },
    {
        "label": "\\color{purple}",
        "insertText": "\\color{purple}",
        "detail": "Màu chữ purple",
        "type": "snippet"
    },
    {
        "label": "\\color{red}",
        "insertText": "\\color{red}",
        "detail": "Màu chữ red",
        "type": "snippet"
    },
    {
        "label": "\\color{teal}",
        "insertText": "\\color{teal}",
        "detail": "Màu chữ teal",
        "type": "snippet"
    },
    {
        "label": "\\color{violet}",
        "insertText": "\\color{violet}",
        "detail": "Màu chữ violet",
        "type": "snippet"
    },
    {
        "label": "\\color{white}",
        "insertText": "\\color{white}",
        "detail": "Màu chữ white",
        "type": "snippet"
    },
    {
        "label": "\\color{yellow}",
        "insertText": "\\color{yellow}",
        "detail": "Màu chữ yellow",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{AnnArbor}",
        "insertText": "\\usetheme{AnnArbor}",
        "detail": "Chủ đề Beamer AnnArbor",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Antibes}",
        "insertText": "\\usetheme{Antibes}",
        "detail": "Chủ đề Beamer Antibes",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Bergen}",
        "insertText": "\\usetheme{Bergen}",
        "detail": "Chủ đề Beamer Bergen",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Berkeley}",
        "insertText": "\\usetheme{Berkeley}",
        "detail": "Chủ đề Beamer Berkeley",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Berlin}",
        "insertText": "\\usetheme{Berlin}",
        "detail": "Chủ đề Beamer Berlin",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Boadilla}",
        "insertText": "\\usetheme{Boadilla}",
        "detail": "Chủ đề Beamer Boadilla",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{CambridgeUS}",
        "insertText": "\\usetheme{CambridgeUS}",
        "detail": "Chủ đề Beamer CambridgeUS",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Copenhagen}",
        "insertText": "\\usetheme{Copenhagen}",
        "detail": "Chủ đề Beamer Copenhagen",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Darmstadt}",
        "insertText": "\\usetheme{Darmstadt}",
        "detail": "Chủ đề Beamer Darmstadt",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Dresden}",
        "insertText": "\\usetheme{Dresden}",
        "detail": "Chủ đề Beamer Dresden",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Frankfurt}",
        "insertText": "\\usetheme{Frankfurt}",
        "detail": "Chủ đề Beamer Frankfurt",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Goettingen}",
        "insertText": "\\usetheme{Goettingen}",
        "detail": "Chủ đề Beamer Goettingen",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Hannover}",
        "insertText": "\\usetheme{Hannover}",
        "detail": "Chủ đề Beamer Hannover",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Ilmenau}",
        "insertText": "\\usetheme{Ilmenau}",
        "detail": "Chủ đề Beamer Ilmenau",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{JuanLesPins}",
        "insertText": "\\usetheme{JuanLesPins}",
        "detail": "Chủ đề Beamer JuanLesPins",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Luebeck}",
        "insertText": "\\usetheme{Luebeck}",
        "detail": "Chủ đề Beamer Luebeck",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Malmoe}",
        "insertText": "\\usetheme{Malmoe}",
        "detail": "Chủ đề Beamer Malmoe",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Marburg}",
        "insertText": "\\usetheme{Marburg}",
        "detail": "Chủ đề Beamer Marburg",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Montpellier}",
        "insertText": "\\usetheme{Montpellier}",
        "detail": "Chủ đề Beamer Montpellier",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{PaloAlto}",
        "insertText": "\\usetheme{PaloAlto}",
        "detail": "Chủ đề Beamer PaloAlto",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Pittsburgh}",
        "insertText": "\\usetheme{Pittsburgh}",
        "detail": "Chủ đề Beamer Pittsburgh",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Rochester}",
        "insertText": "\\usetheme{Rochester}",
        "detail": "Chủ đề Beamer Rochester",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Singapore}",
        "insertText": "\\usetheme{Singapore}",
        "detail": "Chủ đề Beamer Singapore",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Szeged}",
        "insertText": "\\usetheme{Szeged}",
        "detail": "Chủ đề Beamer Szeged",
        "type": "snippet"
    },
    {
        "label": "\\usetheme{Warsaw}",
        "insertText": "\\usetheme{Warsaw}",
        "detail": "Chủ đề Beamer Warsaw",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{albatross}",
        "insertText": "\\usecolortheme{albatross}",
        "detail": "Màu Beamer albatross",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{beetle}",
        "insertText": "\\usecolortheme{beetle}",
        "detail": "Màu Beamer beetle",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{crane}",
        "insertText": "\\usecolortheme{crane}",
        "detail": "Màu Beamer crane",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{default}",
        "insertText": "\\usecolortheme{default}",
        "detail": "Màu Beamer default",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{dolphin}",
        "insertText": "\\usecolortheme{dolphin}",
        "detail": "Màu Beamer dolphin",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{dove}",
        "insertText": "\\usecolortheme{dove}",
        "detail": "Màu Beamer dove",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{fly}",
        "insertText": "\\usecolortheme{fly}",
        "detail": "Màu Beamer fly",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{lily}",
        "insertText": "\\usecolortheme{lily}",
        "detail": "Màu Beamer lily",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{orchid}",
        "insertText": "\\usecolortheme{orchid}",
        "detail": "Màu Beamer orchid",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{rose}",
        "insertText": "\\usecolortheme{rose}",
        "detail": "Màu Beamer rose",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{seagull}",
        "insertText": "\\usecolortheme{seagull}",
        "detail": "Màu Beamer seagull",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{seahorse}",
        "insertText": "\\usecolortheme{seahorse}",
        "detail": "Màu Beamer seahorse",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{sidebartab}",
        "insertText": "\\usecolortheme{sidebartab}",
        "detail": "Màu Beamer sidebartab",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{structure}",
        "insertText": "\\usecolortheme{structure}",
        "detail": "Màu Beamer structure",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{whale}",
        "insertText": "\\usecolortheme{whale}",
        "detail": "Màu Beamer whale",
        "type": "snippet"
    },
    {
        "label": "\\usecolortheme{wolverine}",
        "insertText": "\\usecolortheme{wolverine}",
        "detail": "Màu Beamer wolverine",
        "type": "snippet"
    },
    {
        "label": "\\usefonttheme{default}",
        "insertText": "\\usefonttheme{default}",
        "detail": "Font Beamer default",
        "type": "snippet"
    },
    {
        "label": "\\usefonttheme{professionalfonts}",
        "insertText": "\\usefonttheme{professionalfonts}",
        "detail": "Font Beamer professionalfonts",
        "type": "snippet"
    },
    {
        "label": "\\usefonttheme{structurebold}",
        "insertText": "\\usefonttheme{structurebold}",
        "detail": "Font Beamer structurebold",
        "type": "snippet"
    },
    {
        "label": "\\usefonttheme{structureitalicserif}",
        "insertText": "\\usefonttheme{structureitalicserif}",
        "detail": "Font Beamer structureitalicserif",
        "type": "snippet"
    },
    {
        "label": "\\usefonttheme{structuresmallcapsserif}",
        "insertText": "\\usefonttheme{structuresmallcapsserif}",
        "detail": "Font Beamer structuresmallcapsserif",
        "type": "snippet"
    },
    {
        "label": "\\useinnertheme{circles}",
        "insertText": "\\useinnertheme{circles}",
        "detail": "Theme trong Beamer circles",
        "type": "snippet"
    },
    {
        "label": "\\useinnertheme{default}",
        "insertText": "\\useinnertheme{default}",
        "detail": "Theme trong Beamer default",
        "type": "snippet"
    },
    {
        "label": "\\useinnertheme{inmargin}",
        "insertText": "\\useinnertheme{inmargin}",
        "detail": "Theme trong Beamer inmargin",
        "type": "snippet"
    },
    {
        "label": "\\useinnertheme{rectangles}",
        "insertText": "\\useinnertheme{rectangles}",
        "detail": "Theme trong Beamer rectangles",
        "type": "snippet"
    },
    {
        "label": "\\useinnertheme{rounded}",
        "insertText": "\\useinnertheme{rounded}",
        "detail": "Theme trong Beamer rounded",
        "type": "snippet"
    },
    {
        "label": "\\useoutertheme{default}",
        "insertText": "\\useoutertheme{default}",
        "detail": "Theme ngoài Beamer default",
        "type": "snippet"
    },
    {
        "label": "\\useoutertheme{infolines}",
        "insertText": "\\useoutertheme{infolines}",
        "detail": "Theme ngoài Beamer infolines",
        "type": "snippet"
    },
    {
        "label": "\\useoutertheme{miniframes}",
        "insertText": "\\useoutertheme{miniframes}",
        "detail": "Theme ngoài Beamer miniframes",
        "type": "snippet"
    },
    {
        "label": "\\useoutertheme{shadow}",
        "insertText": "\\useoutertheme{shadow}",
        "detail": "Theme ngoài Beamer shadow",
        "type": "snippet"
    },
    {
        "label": "\\useoutertheme{sidebar}",
        "insertText": "\\useoutertheme{sidebar}",
        "detail": "Theme ngoài Beamer sidebar",
        "type": "snippet"
    },
    {
        "label": "\\useoutertheme{smoothbars}",
        "insertText": "\\useoutertheme{smoothbars}",
        "detail": "Theme ngoài Beamer smoothbars",
        "type": "snippet"
    },
    {
        "label": "\\useoutertheme{smoothtree}",
        "insertText": "\\useoutertheme{smoothtree}",
        "detail": "Theme ngoài Beamer smoothtree",
        "type": "snippet"
    },
    {
        "label": "\\useoutertheme{split}",
        "insertText": "\\useoutertheme{split}",
        "detail": "Theme ngoài Beamer split",
        "type": "snippet"
    },
    {
        "label": "\\useoutertheme{tree}",
        "insertText": "\\useoutertheme{tree}",
        "detail": "Theme ngoài Beamer tree",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{arrows}",
        "insertText": "\\usetikzlibrary{arrows}",
        "detail": "Thư viện TikZ arrows",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{automata}",
        "insertText": "\\usetikzlibrary{automata}",
        "detail": "Thư viện TikZ automata",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{backgrounds}",
        "insertText": "\\usetikzlibrary{backgrounds}",
        "detail": "Thư viện TikZ backgrounds",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{calc}",
        "insertText": "\\usetikzlibrary{calc}",
        "detail": "Thư viện TikZ calc",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{calendar}",
        "insertText": "\\usetikzlibrary{calendar}",
        "detail": "Thư viện TikZ calendar",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{chains}",
        "insertText": "\\usetikzlibrary{chains}",
        "detail": "Thư viện TikZ chains",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{circuits}",
        "insertText": "\\usetikzlibrary{circuits}",
        "detail": "Thư viện TikZ circuits",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{decorations}",
        "insertText": "\\usetikzlibrary{decorations}",
        "detail": "Thư viện TikZ decorations",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{er}",
        "insertText": "\\usetikzlibrary{er}",
        "detail": "Thư viện TikZ er",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{fit}",
        "insertText": "\\usetikzlibrary{fit}",
        "detail": "Thư viện TikZ fit",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{folding}",
        "insertText": "\\usetikzlibrary{folding}",
        "detail": "Thư viện TikZ folding",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{intersections}",
        "insertText": "\\usetikzlibrary{intersections}",
        "detail": "Thư viện TikZ intersections",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{matrix}",
        "insertText": "\\usetikzlibrary{matrix}",
        "detail": "Thư viện TikZ matrix",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{patterns}",
        "insertText": "\\usetikzlibrary{patterns}",
        "detail": "Thư viện TikZ patterns",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{petri}",
        "insertText": "\\usetikzlibrary{petri}",
        "detail": "Thư viện TikZ petri",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{plotmarks}",
        "insertText": "\\usetikzlibrary{plotmarks}",
        "detail": "Thư viện TikZ plotmarks",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{shadows}",
        "insertText": "\\usetikzlibrary{shadows}",
        "detail": "Thư viện TikZ shadows",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{shapes}",
        "insertText": "\\usetikzlibrary{shapes}",
        "detail": "Thư viện TikZ shapes",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{spy}",
        "insertText": "\\usetikzlibrary{spy}",
        "detail": "Thư viện TikZ spy",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{svg.path}",
        "insertText": "\\usetikzlibrary{svg.path}",
        "detail": "Thư viện TikZ svg.path",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{trees}",
        "insertText": "\\usetikzlibrary{trees}",
        "detail": "Thư viện TikZ trees",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{topaths}",
        "insertText": "\\usetikzlibrary{topaths}",
        "detail": "Thư viện TikZ topaths",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{3d}",
        "insertText": "\\usetikzlibrary{3d}",
        "detail": "Thư viện TikZ 3d",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{angles}",
        "insertText": "\\usetikzlibrary{angles}",
        "detail": "Thư viện TikZ angles",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{babel}",
        "insertText": "\\usetikzlibrary{babel}",
        "detail": "Thư viện TikZ babel",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{bending}",
        "insertText": "\\usetikzlibrary{bending}",
        "detail": "Thư viện TikZ bending",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{circuits.ee.IEC}",
        "insertText": "\\usetikzlibrary{circuits.ee.IEC}",
        "detail": "Thư viện TikZ circuits.ee.IEC",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{circuits.logic.IEC}",
        "insertText": "\\usetikzlibrary{circuits.logic.IEC}",
        "detail": "Thư viện TikZ circuits.logic.IEC",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{circuits.logic.CDH}",
        "insertText": "\\usetikzlibrary{circuits.logic.CDH}",
        "detail": "Thư viện TikZ circuits.logic.CDH",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{decorations.fractals}",
        "insertText": "\\usetikzlibrary{decorations.fractals}",
        "detail": "Thư viện TikZ decorations.fractals",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{decorations.markings}",
        "insertText": "\\usetikzlibrary{decorations.markings}",
        "detail": "Thư viện TikZ decorations.markings",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{decorations.pathreplacing}",
        "insertText": "\\usetikzlibrary{decorations.pathreplacing}",
        "detail": "Thư viện TikZ decorations.pathreplacing",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{decorations.shapes}",
        "insertText": "\\usetikzlibrary{decorations.shapes}",
        "detail": "Thư viện TikZ decorations.shapes",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{decorations.text}",
        "insertText": "\\usetikzlibrary{decorations.text}",
        "detail": "Thư viện TikZ decorations.text",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{external}",
        "insertText": "\\usetikzlibrary{external}",
        "detail": "Thư viện TikZ external",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{fadings}",
        "insertText": "\\usetikzlibrary{fadings}",
        "detail": "Thư viện TikZ fadings",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{graphs}",
        "insertText": "\\usetikzlibrary{graphs}",
        "detail": "Thư viện TikZ graphs",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{graphs.standard}",
        "insertText": "\\usetikzlibrary{graphs.standard}",
        "detail": "Thư viện TikZ graphs.standard",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{lindenmayersystems}",
        "insertText": "\\usetikzlibrary{lindenmayersystems}",
        "detail": "Thư viện TikZ lindenmayersystems",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{math}",
        "insertText": "\\usetikzlibrary{math}",
        "detail": "Thư viện TikZ math",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{quotes}",
        "insertText": "\\usetikzlibrary{quotes}",
        "detail": "Thư viện TikZ quotes",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{scopes}",
        "insertText": "\\usetikzlibrary{scopes}",
        "detail": "Thư viện TikZ scopes",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{through}",
        "insertText": "\\usetikzlibrary{through}",
        "detail": "Thư viện TikZ through",
        "type": "snippet"
    },
    {
        "label": "\\usetikzlibrary{views}",
        "insertText": "\\usetikzlibrary{views}",
        "detail": "Thư viện TikZ views",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{afrikaans}{arg1}",
        "insertText": "\\foreignlanguage{afrikaans}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Afrikaans (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{afrikaans}",
        "insertText": "\\setotherlanguage{afrikaans}",
        "detail": "Khai báo tiếng Afrikaans (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{arabic}{arg1}",
        "insertText": "\\foreignlanguage{arabic}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Arabic (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{arabic}",
        "insertText": "\\setotherlanguage{arabic}",
        "detail": "Khai báo tiếng Arabic (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{basque}{arg1}",
        "insertText": "\\foreignlanguage{basque}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Basque (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{basque}",
        "insertText": "\\setotherlanguage{basque}",
        "detail": "Khai báo tiếng Basque (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{bulgarian}{arg1}",
        "insertText": "\\foreignlanguage{bulgarian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Bulgarian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{bulgarian}",
        "insertText": "\\setotherlanguage{bulgarian}",
        "detail": "Khai báo tiếng Bulgarian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{catalan}{arg1}",
        "insertText": "\\foreignlanguage{catalan}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Catalan (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{catalan}",
        "insertText": "\\setotherlanguage{catalan}",
        "detail": "Khai báo tiếng Catalan (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{croatian}{arg1}",
        "insertText": "\\foreignlanguage{croatian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Croatian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{croatian}",
        "insertText": "\\setotherlanguage{croatian}",
        "detail": "Khai báo tiếng Croatian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{czech}{arg1}",
        "insertText": "\\foreignlanguage{czech}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Czech (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{czech}",
        "insertText": "\\setotherlanguage{czech}",
        "detail": "Khai báo tiếng Czech (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{danish}{arg1}",
        "insertText": "\\foreignlanguage{danish}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Danish (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{danish}",
        "insertText": "\\setotherlanguage{danish}",
        "detail": "Khai báo tiếng Danish (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{dutch}{arg1}",
        "insertText": "\\foreignlanguage{dutch}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Dutch (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{dutch}",
        "insertText": "\\setotherlanguage{dutch}",
        "detail": "Khai báo tiếng Dutch (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{english}{arg1}",
        "insertText": "\\foreignlanguage{english}{${1:arg1}}",
        "detail": "Đoạn văn tiếng English (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{english}",
        "insertText": "\\setotherlanguage{english}",
        "detail": "Khai báo tiếng English (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{esperanto}{arg1}",
        "insertText": "\\foreignlanguage{esperanto}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Esperanto (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{esperanto}",
        "insertText": "\\setotherlanguage{esperanto}",
        "detail": "Khai báo tiếng Esperanto (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{estonian}{arg1}",
        "insertText": "\\foreignlanguage{estonian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Estonian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{estonian}",
        "insertText": "\\setotherlanguage{estonian}",
        "detail": "Khai báo tiếng Estonian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{finnish}{arg1}",
        "insertText": "\\foreignlanguage{finnish}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Finnish (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{finnish}",
        "insertText": "\\setotherlanguage{finnish}",
        "detail": "Khai báo tiếng Finnish (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{french}{arg1}",
        "insertText": "\\foreignlanguage{french}{${1:arg1}}",
        "detail": "Đoạn văn tiếng French (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{french}",
        "insertText": "\\setotherlanguage{french}",
        "detail": "Khai báo tiếng French (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{galician}{arg1}",
        "insertText": "\\foreignlanguage{galician}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Galician (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{galician}",
        "insertText": "\\setotherlanguage{galician}",
        "detail": "Khai báo tiếng Galician (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{german}{arg1}",
        "insertText": "\\foreignlanguage{german}{${1:arg1}}",
        "detail": "Đoạn văn tiếng German (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{german}",
        "insertText": "\\setotherlanguage{german}",
        "detail": "Khai báo tiếng German (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{greek}{arg1}",
        "insertText": "\\foreignlanguage{greek}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Greek (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{greek}",
        "insertText": "\\setotherlanguage{greek}",
        "detail": "Khai báo tiếng Greek (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{hebrew}{arg1}",
        "insertText": "\\foreignlanguage{hebrew}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Hebrew (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{hebrew}",
        "insertText": "\\setotherlanguage{hebrew}",
        "detail": "Khai báo tiếng Hebrew (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{hungarian}{arg1}",
        "insertText": "\\foreignlanguage{hungarian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Hungarian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{hungarian}",
        "insertText": "\\setotherlanguage{hungarian}",
        "detail": "Khai báo tiếng Hungarian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{icelandic}{arg1}",
        "insertText": "\\foreignlanguage{icelandic}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Icelandic (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{icelandic}",
        "insertText": "\\setotherlanguage{icelandic}",
        "detail": "Khai báo tiếng Icelandic (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{indonesian}{arg1}",
        "insertText": "\\foreignlanguage{indonesian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Indonesian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{indonesian}",
        "insertText": "\\setotherlanguage{indonesian}",
        "detail": "Khai báo tiếng Indonesian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{interlingua}{arg1}",
        "insertText": "\\foreignlanguage{interlingua}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Interlingua (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{interlingua}",
        "insertText": "\\setotherlanguage{interlingua}",
        "detail": "Khai báo tiếng Interlingua (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{irish}{arg1}",
        "insertText": "\\foreignlanguage{irish}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Irish (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{irish}",
        "insertText": "\\setotherlanguage{irish}",
        "detail": "Khai báo tiếng Irish (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{italian}{arg1}",
        "insertText": "\\foreignlanguage{italian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Italian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{italian}",
        "insertText": "\\setotherlanguage{italian}",
        "detail": "Khai báo tiếng Italian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{japanese}{arg1}",
        "insertText": "\\foreignlanguage{japanese}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Japanese (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{japanese}",
        "insertText": "\\setotherlanguage{japanese}",
        "detail": "Khai báo tiếng Japanese (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{korean}{arg1}",
        "insertText": "\\foreignlanguage{korean}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Korean (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{korean}",
        "insertText": "\\setotherlanguage{korean}",
        "detail": "Khai báo tiếng Korean (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{latin}{arg1}",
        "insertText": "\\foreignlanguage{latin}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Latin (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{latin}",
        "insertText": "\\setotherlanguage{latin}",
        "detail": "Khai báo tiếng Latin (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{latvian}{arg1}",
        "insertText": "\\foreignlanguage{latvian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Latvian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{latvian}",
        "insertText": "\\setotherlanguage{latvian}",
        "detail": "Khai báo tiếng Latvian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{lithuanian}{arg1}",
        "insertText": "\\foreignlanguage{lithuanian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Lithuanian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{lithuanian}",
        "insertText": "\\setotherlanguage{lithuanian}",
        "detail": "Khai báo tiếng Lithuanian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{malay}{arg1}",
        "insertText": "\\foreignlanguage{malay}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Malay (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{malay}",
        "insertText": "\\setotherlanguage{malay}",
        "detail": "Khai báo tiếng Malay (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{mongolian}{arg1}",
        "insertText": "\\foreignlanguage{mongolian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Mongolian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{mongolian}",
        "insertText": "\\setotherlanguage{mongolian}",
        "detail": "Khai báo tiếng Mongolian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{norwegian}{arg1}",
        "insertText": "\\foreignlanguage{norwegian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Norwegian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{norwegian}",
        "insertText": "\\setotherlanguage{norwegian}",
        "detail": "Khai báo tiếng Norwegian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{persian}{arg1}",
        "insertText": "\\foreignlanguage{persian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Persian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{persian}",
        "insertText": "\\setotherlanguage{persian}",
        "detail": "Khai báo tiếng Persian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{polish}{arg1}",
        "insertText": "\\foreignlanguage{polish}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Polish (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{polish}",
        "insertText": "\\setotherlanguage{polish}",
        "detail": "Khai báo tiếng Polish (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{portuguese}{arg1}",
        "insertText": "\\foreignlanguage{portuguese}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Portuguese (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{portuguese}",
        "insertText": "\\setotherlanguage{portuguese}",
        "detail": "Khai báo tiếng Portuguese (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{romanian}{arg1}",
        "insertText": "\\foreignlanguage{romanian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Romanian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{romanian}",
        "insertText": "\\setotherlanguage{romanian}",
        "detail": "Khai báo tiếng Romanian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{russian}{arg1}",
        "insertText": "\\foreignlanguage{russian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Russian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{russian}",
        "insertText": "\\setotherlanguage{russian}",
        "detail": "Khai báo tiếng Russian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{sami}{arg1}",
        "insertText": "\\foreignlanguage{sami}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Sami (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{sami}",
        "insertText": "\\setotherlanguage{sami}",
        "detail": "Khai báo tiếng Sami (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{scottish}{arg1}",
        "insertText": "\\foreignlanguage{scottish}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Scottish (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{scottish}",
        "insertText": "\\setotherlanguage{scottish}",
        "detail": "Khai báo tiếng Scottish (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{serbian}{arg1}",
        "insertText": "\\foreignlanguage{serbian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Serbian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{serbian}",
        "insertText": "\\setotherlanguage{serbian}",
        "detail": "Khai báo tiếng Serbian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{slovak}{arg1}",
        "insertText": "\\foreignlanguage{slovak}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Slovak (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{slovak}",
        "insertText": "\\setotherlanguage{slovak}",
        "detail": "Khai báo tiếng Slovak (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{slovenian}{arg1}",
        "insertText": "\\foreignlanguage{slovenian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Slovenian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{slovenian}",
        "insertText": "\\setotherlanguage{slovenian}",
        "detail": "Khai báo tiếng Slovenian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{spanish}{arg1}",
        "insertText": "\\foreignlanguage{spanish}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Spanish (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{spanish}",
        "insertText": "\\setotherlanguage{spanish}",
        "detail": "Khai báo tiếng Spanish (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{swedish}{arg1}",
        "insertText": "\\foreignlanguage{swedish}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Swedish (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{swedish}",
        "insertText": "\\setotherlanguage{swedish}",
        "detail": "Khai báo tiếng Swedish (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{thai}{arg1}",
        "insertText": "\\foreignlanguage{thai}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Thai (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{thai}",
        "insertText": "\\setotherlanguage{thai}",
        "detail": "Khai báo tiếng Thai (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{turkish}{arg1}",
        "insertText": "\\foreignlanguage{turkish}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Turkish (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{turkish}",
        "insertText": "\\setotherlanguage{turkish}",
        "detail": "Khai báo tiếng Turkish (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{ukrainian}{arg1}",
        "insertText": "\\foreignlanguage{ukrainian}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Ukrainian (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{ukrainian}",
        "insertText": "\\setotherlanguage{ukrainian}",
        "detail": "Khai báo tiếng Ukrainian (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{vietnamese}{arg1}",
        "insertText": "\\foreignlanguage{vietnamese}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Vietnamese (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{vietnamese}",
        "insertText": "\\setotherlanguage{vietnamese}",
        "detail": "Khai báo tiếng Vietnamese (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\foreignlanguage{welsh}{arg1}",
        "insertText": "\\foreignlanguage{welsh}{${1:arg1}}",
        "detail": "Đoạn văn tiếng Welsh (Babel)",
        "type": "snippet"
    },
    {
        "label": "\\setotherlanguage{welsh}",
        "insertText": "\\setotherlanguage{welsh}",
        "detail": "Khai báo tiếng Welsh (Polyglossia)",
        "type": "snippet"
    },
    {
        "label": "\\columnseprule",
        "insertText": "\\columnseprule",
        "detail": "Thuộc tính độ dài \\columnseprule",
        "type": "snippet"
    },
    {
        "label": "\\baselineskip",
        "insertText": "\\baselineskip",
        "detail": "Thuộc tính độ dài \\baselineskip",
        "type": "snippet"
    },
    {
        "label": "\\evensidemargin",
        "insertText": "\\evensidemargin",
        "detail": "Thuộc tính độ dài \\evensidemargin",
        "type": "snippet"
    },
    {
        "label": "\\oddsidemargin",
        "insertText": "\\oddsidemargin",
        "detail": "Thuộc tính độ dài \\oddsidemargin",
        "type": "snippet"
    },
    {
        "label": "\\topmargin",
        "insertText": "\\topmargin",
        "detail": "Thuộc tính độ dài \\topmargin",
        "type": "snippet"
    },
    {
        "label": "\\headheight",
        "insertText": "\\headheight",
        "detail": "Thuộc tính độ dài \\headheight",
        "type": "snippet"
    },
    {
        "label": "\\headsep",
        "insertText": "\\headsep",
        "detail": "Thuộc tính độ dài \\headsep",
        "type": "snippet"
    },
    {
        "label": "\\footskip",
        "insertText": "\\footskip",
        "detail": "Thuộc tính độ dài \\footskip",
        "type": "snippet"
    },
    {
        "label": "\\marginparwidth",
        "insertText": "\\marginparwidth",
        "detail": "Thuộc tính độ dài \\marginparwidth",
        "type": "snippet"
    },
    {
        "label": "\\marginparsep",
        "insertText": "\\marginparsep",
        "detail": "Thuộc tính độ dài \\marginparsep",
        "type": "snippet"
    },
    {
        "label": "\\becquerel",
        "insertText": "\\becquerel",
        "detail": "Đơn vị Vật lý SI becquerel",
        "type": "snippet"
    },
    {
        "label": "\\coulomb",
        "insertText": "\\coulomb",
        "detail": "Đơn vị Vật lý SI coulomb",
        "type": "snippet"
    },
    {
        "label": "\\farad",
        "insertText": "\\farad",
        "detail": "Đơn vị Vật lý SI farad",
        "type": "snippet"
    },
    {
        "label": "\\gray",
        "insertText": "\\gray",
        "detail": "Đơn vị Vật lý SI gray",
        "type": "snippet"
    },
    {
        "label": "\\hertz",
        "insertText": "\\hertz",
        "detail": "Đơn vị Vật lý SI hertz",
        "type": "snippet"
    },
    {
        "label": "\\henry",
        "insertText": "\\henry",
        "detail": "Đơn vị Vật lý SI henry",
        "type": "snippet"
    },
    {
        "label": "\\joule",
        "insertText": "\\joule",
        "detail": "Đơn vị Vật lý SI joule",
        "type": "snippet"
    },
    {
        "label": "\\lumen",
        "insertText": "\\lumen",
        "detail": "Đơn vị Vật lý SI lumen",
        "type": "snippet"
    },
    {
        "label": "\\katal",
        "insertText": "\\katal",
        "detail": "Đơn vị Vật lý SI katal",
        "type": "snippet"
    },
    {
        "label": "\\ohm",
        "insertText": "\\ohm",
        "detail": "Đơn vị Vật lý SI ohm",
        "type": "snippet"
    },
    {
        "label": "\\radian",
        "insertText": "\\radian",
        "detail": "Đơn vị Vật lý SI radian",
        "type": "snippet"
    },
    {
        "label": "\\siemens",
        "insertText": "\\siemens",
        "detail": "Đơn vị Vật lý SI siemens",
        "type": "snippet"
    },
    {
        "label": "\\sievert",
        "insertText": "\\sievert",
        "detail": "Đơn vị Vật lý SI sievert",
        "type": "snippet"
    },
    {
        "label": "\\steradian",
        "insertText": "\\steradian",
        "detail": "Đơn vị Vật lý SI steradian",
        "type": "snippet"
    },
    {
        "label": "\\tesla",
        "insertText": "\\tesla",
        "detail": "Đơn vị Vật lý SI tesla",
        "type": "snippet"
    },
    {
        "label": "\\volt",
        "insertText": "\\volt",
        "detail": "Đơn vị Vật lý SI volt",
        "type": "snippet"
    },
    {
        "label": "\\watt",
        "insertText": "\\watt",
        "detail": "Đơn vị Vật lý SI watt",
        "type": "snippet"
    },
    {
        "label": "\\weber",
        "insertText": "\\weber",
        "detail": "Đơn vị Vật lý SI weber",
        "type": "snippet"
    },
    {
        "label": "\\deca",
        "insertText": "\\deca",
        "detail": "Tiền tố SI deca",
        "type": "snippet"
    },
    {
        "label": "\\hecto",
        "insertText": "\\hecto",
        "detail": "Tiền tố SI hecto",
        "type": "snippet"
    },
    {
        "label": "\\kilo",
        "insertText": "\\kilo",
        "detail": "Tiền tố SI kilo",
        "type": "snippet"
    },
    {
        "label": "\\mega",
        "insertText": "\\mega",
        "detail": "Tiền tố SI mega",
        "type": "snippet"
    },
    {
        "label": "\\giga",
        "insertText": "\\giga",
        "detail": "Tiền tố SI giga",
        "type": "snippet"
    },
    {
        "label": "\\tera",
        "insertText": "\\tera",
        "detail": "Tiền tố SI tera",
        "type": "snippet"
    },
    {
        "label": "\\peta",
        "insertText": "\\peta",
        "detail": "Tiền tố SI peta",
        "type": "snippet"
    },
    {
        "label": "\\exa",
        "insertText": "\\exa",
        "detail": "Tiền tố SI exa",
        "type": "snippet"
    },
    {
        "label": "\\zetta",
        "insertText": "\\zetta",
        "detail": "Tiền tố SI zetta",
        "type": "snippet"
    },
    {
        "label": "\\yotta",
        "insertText": "\\yotta",
        "detail": "Tiền tố SI yotta",
        "type": "snippet"
    },
    {
        "label": "\\deci",
        "insertText": "\\deci",
        "detail": "Tiền tố SI deci",
        "type": "snippet"
    },
    {
        "label": "\\centi",
        "insertText": "\\centi",
        "detail": "Tiền tố SI centi",
        "type": "snippet"
    },
    {
        "label": "\\milli",
        "insertText": "\\milli",
        "detail": "Tiền tố SI milli",
        "type": "snippet"
    },
    {
        "label": "\\micro",
        "insertText": "\\micro",
        "detail": "Tiền tố SI micro",
        "type": "snippet"
    },
    {
        "label": "\\nano",
        "insertText": "\\nano",
        "detail": "Tiền tố SI nano",
        "type": "snippet"
    },
    {
        "label": "\\pico",
        "insertText": "\\pico",
        "detail": "Tiền tố SI pico",
        "type": "snippet"
    },
    {
        "label": "\\femto",
        "insertText": "\\femto",
        "detail": "Tiền tố SI femto",
        "type": "snippet"
    },
    {
        "label": "\\atto",
        "insertText": "\\atto",
        "detail": "Tiền tố SI atto",
        "type": "snippet"
    },
    {
        "label": "\\zepto",
        "insertText": "\\zepto",
        "detail": "Tiền tố SI zepto",
        "type": "snippet"
    },
    {
        "label": "\\yocto",
        "insertText": "\\yocto",
        "detail": "Tiền tố SI yocto",
        "type": "snippet"
    },
    {
        "label": "\\prec",
        "insertText": "\\prec",
        "detail": "Quan hệ \\prec",
        "type": "snippet"
    },
    {
        "label": "\\succ",
        "insertText": "\\succ",
        "detail": "Quan hệ \\succ",
        "type": "snippet"
    },
    {
        "label": "\\preceq",
        "insertText": "\\preceq",
        "detail": "Quan hệ \\preceq",
        "type": "snippet"
    },
    {
        "label": "\\succeq",
        "insertText": "\\succeq",
        "detail": "Quan hệ \\succeq",
        "type": "snippet"
    },
    {
        "label": "\\bowtie",
        "insertText": "\\bowtie",
        "detail": "Quan hệ \\bowtie",
        "type": "snippet"
    },
    {
        "label": "\\sqsubset",
        "insertText": "\\sqsubset",
        "detail": "Quan hệ \\sqsubset",
        "type": "snippet"
    },
    {
        "label": "\\sqsupset",
        "insertText": "\\sqsupset",
        "detail": "Quan hệ \\sqsupset",
        "type": "snippet"
    },
    {
        "label": "\\smile",
        "insertText": "\\smile",
        "detail": "Quan hệ \\smile",
        "type": "snippet"
    },
    {
        "label": "\\sqsubseteq",
        "insertText": "\\sqsubseteq",
        "detail": "Quan hệ \\sqsubseteq",
        "type": "snippet"
    },
    {
        "label": "\\sqsupseteq",
        "insertText": "\\sqsupseteq",
        "detail": "Quan hệ \\sqsupseteq",
        "type": "snippet"
    },
    {
        "label": "\\frown",
        "insertText": "\\frown",
        "detail": "Quan hệ \\frown",
        "type": "snippet"
    },
    {
        "label": "\\ni",
        "insertText": "\\ni",
        "detail": "Quan hệ \\ni",
        "type": "snippet"
    },
    {
        "label": "\\triangleleft",
        "insertText": "\\triangleleft",
        "detail": "Dấu toán học \\triangleleft",
        "type": "snippet"
    },
    {
        "label": "\\triangleright",
        "insertText": "\\triangleright",
        "detail": "Dấu toán học \\triangleright",
        "type": "snippet"
    },
    {
        "label": "\\wr",
        "insertText": "\\wr",
        "detail": "Dấu toán học \\wr",
        "type": "snippet"
    },
    {
        "label": "\\bigcirc",
        "insertText": "\\bigcirc",
        "detail": "Dấu toán học \\bigcirc",
        "type": "snippet"
    },
    {
        "label": "\\bigtriangleup",
        "insertText": "\\bigtriangleup",
        "detail": "Dấu toán học \\bigtriangleup",
        "type": "snippet"
    },
    {
        "label": "\\bigtriangledown",
        "insertText": "\\bigtriangledown",
        "detail": "Dấu toán học \\bigtriangledown",
        "type": "snippet"
    },
    {
        "label": "\\lhd",
        "insertText": "\\lhd",
        "detail": "Dấu toán học \\lhd",
        "type": "snippet"
    },
    {
        "label": "\\rhd",
        "insertText": "\\rhd",
        "detail": "Dấu toán học \\rhd",
        "type": "snippet"
    },
    {
        "label": "\\unlhd",
        "insertText": "\\unlhd",
        "detail": "Dấu toán học \\unlhd",
        "type": "snippet"
    },
    {
        "label": "\\unrhd",
        "insertText": "\\unrhd",
        "detail": "Dấu toán học \\unrhd",
        "type": "snippet"
    },
    {
        "label": "\\amalg",
        "insertText": "\\amalg",
        "detail": "Dấu toán học \\amalg",
        "type": "snippet"
    },
    {
        "label": "\\hookleftarrow",
        "insertText": "\\hookleftarrow",
        "detail": "Mũi tên \\hookleftarrow",
        "type": "snippet"
    },
    {
        "label": "\\hookrightarrow",
        "insertText": "\\hookrightarrow",
        "detail": "Mũi tên \\hookrightarrow",
        "type": "snippet"
    },
    {
        "label": "\\updownarrow",
        "insertText": "\\updownarrow",
        "detail": "Mũi tên \\updownarrow",
        "type": "snippet"
    },
    {
        "label": "\\bigodot",
        "insertText": "\\bigodot",
        "detail": "Hàm \\bigodot",
        "type": "snippet"
    },
    {
        "label": "\\pagestyle{arg1}",
        "insertText": "\\pagestyle{${1:arg1}}",
        "detail": "Style trang \\pagestyle",
        "type": "snippet"
    },
    {
        "label": "\\thispagestyle{arg1}",
        "insertText": "\\thispagestyle{${1:arg1}}",
        "detail": "Trang hiện tại \\thispagestyle",
        "type": "snippet"
    },
    {
        "label": "\\marginpar{arg1}",
        "insertText": "\\marginpar{${1:arg1}}",
        "detail": "Ghi chú lề \\marginpar",
        "type": "snippet"
    },
    {
        "label": "\\verb++",
        "insertText": "\\verb++",
        "detail": "Văn bản mã thô \\verb",
        "type": "snippet"
    },
    {
        "label": "\\hspace{arg1}",
        "insertText": "\\hspace{${1:arg1}}",
        "detail": "Khoảng trắng \\hspace",
        "type": "snippet"
    },
    {
        "label": "\\vspace{arg1}",
        "insertText": "\\vspace{${1:arg1}}",
        "detail": "Khoảng dọc \\vspace",
        "type": "snippet"
    },
    {
        "label": "\\dotfill",
        "insertText": "\\dotfill",
        "detail": "Dấu chấm lấp đầy \\dotfill",
        "type": "snippet"
    },
    {
        "label": "\\hrulefill",
        "insertText": "\\hrulefill",
        "detail": "Gạch lấp đầy \\hrulefill",
        "type": "snippet"
    },
    {
        "label": "\\rule{arg1}{arg2}",
        "insertText": "\\rule{${1:arg1}}{${2:arg2}}",
        "detail": "Vẽ đường thẳng \\rule",
        "type": "snippet"
    },
    {
        "label": "\\cline{arg1}",
        "insertText": "\\cline{${1:arg1}}",
        "detail": "Kẻ đa cột \\cline",
        "type": "snippet"
    },
    {
        "label": "\\multicolumn{arg1}{arg2}arg3",
        "insertText": "\\multicolumn{${1:arg1}}{${2:arg2}}${3:arg3}",
        "detail": "Gộp cột \\multicolumn",
        "type": "snippet"
    },
    {
        "label": "\\grid",
        "insertText": "\\grid",
        "detail": "Vẽ lưới \\grid",
        "type": "snippet"
    },
    {
        "label": "\\frametitle{arg1}",
        "insertText": "\\frametitle{${1:arg1}}",
        "detail": "Tiêu đề Frame \\frametitle",
        "type": "snippet"
    },
    {
        "label": "\\framesubtitle{arg1}",
        "insertText": "\\framesubtitle{${1:arg1}}",
        "detail": "Phụ đề Frame \\framesubtitle",
        "type": "snippet"
    },
    {
        "label": "\\alert{arg1}",
        "insertText": "\\alert{${1:arg1}}",
        "detail": "Nổi chữ \\alert",
        "type": "snippet"
    },
    {
        "label": "\\alt<2>arg1arg2",
        "insertText": "\\alt<2>${1:arg1}{${2:arg2}}",
        "detail": "Thay thế \\alt",
        "type": "snippet"
    },
    {
        "label": "\\column{arg1}",
        "insertText": "\\column{${1:arg1}}",
        "detail": "Sử dụng column \\column",
        "type": "snippet"
    },
    {
        "label": "\\chemfig{*6(-=-=-=)}",
        "insertText": "\\chemfig{*6(-=-=-=)}",
        "detail": "Vòng 6 Benzen",
        "type": "snippet"
    },
    {
        "label": "\\ce{(g)}",
        "insertText": "\\ce{(g)}",
        "detail": "Trạng thái khí \\ce{(g)}",
        "type": "snippet"
    },
    {
        "label": "\\ce{(s)}",
        "insertText": "\\ce{(s)}",
        "detail": "Trạng thái rắn \\ce{(s)}",
        "type": "snippet"
    },
    {
        "label": "\\ce{(l)}",
        "insertText": "\\ce{(l)}",
        "detail": "Trạng thái lỏng \\ce{(l)}",
        "type": "snippet"
    },
    {
        "label": "\\color{AliceBlue}",
        "insertText": "\\color{AliceBlue}",
        "detail": "Màu nâng cao AliceBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{AntiqueWhite}",
        "insertText": "\\color{AntiqueWhite}",
        "detail": "Màu nâng cao AntiqueWhite (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Aqua}",
        "insertText": "\\color{Aqua}",
        "detail": "Màu nâng cao Aqua (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Aquamarine}",
        "insertText": "\\color{Aquamarine}",
        "detail": "Màu nâng cao Aquamarine (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Azure}",
        "insertText": "\\color{Azure}",
        "detail": "Màu nâng cao Azure (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Beige}",
        "insertText": "\\color{Beige}",
        "detail": "Màu nâng cao Beige (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Bisque}",
        "insertText": "\\color{Bisque}",
        "detail": "Màu nâng cao Bisque (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{BlanchedAlmond}",
        "insertText": "\\color{BlanchedAlmond}",
        "detail": "Màu nâng cao BlanchedAlmond (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{BlueViolet}",
        "insertText": "\\color{BlueViolet}",
        "detail": "Màu nâng cao BlueViolet (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Brown}",
        "insertText": "\\color{Brown}",
        "detail": "Màu nâng cao Brown (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{BurlyWood}",
        "insertText": "\\color{BurlyWood}",
        "detail": "Màu nâng cao BurlyWood (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{CadetBlue}",
        "insertText": "\\color{CadetBlue}",
        "detail": "Màu nâng cao CadetBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Chartreuse}",
        "insertText": "\\color{Chartreuse}",
        "detail": "Màu nâng cao Chartreuse (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Chocolate}",
        "insertText": "\\color{Chocolate}",
        "detail": "Màu nâng cao Chocolate (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Coral}",
        "insertText": "\\color{Coral}",
        "detail": "Màu nâng cao Coral (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{CornflowerBlue}",
        "insertText": "\\color{CornflowerBlue}",
        "detail": "Màu nâng cao CornflowerBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Cornsilk}",
        "insertText": "\\color{Cornsilk}",
        "detail": "Màu nâng cao Cornsilk (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Crimson}",
        "insertText": "\\color{Crimson}",
        "detail": "Màu nâng cao Crimson (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Cyan}",
        "insertText": "\\color{Cyan}",
        "detail": "Màu nâng cao Cyan (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkBlue}",
        "insertText": "\\color{DarkBlue}",
        "detail": "Màu nâng cao DarkBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkCyan}",
        "insertText": "\\color{DarkCyan}",
        "detail": "Màu nâng cao DarkCyan (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkGoldenrod}",
        "insertText": "\\color{DarkGoldenrod}",
        "detail": "Màu nâng cao DarkGoldenrod (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkGray}",
        "insertText": "\\color{DarkGray}",
        "detail": "Màu nâng cao DarkGray (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkGreen}",
        "insertText": "\\color{DarkGreen}",
        "detail": "Màu nâng cao DarkGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkGrey}",
        "insertText": "\\color{DarkGrey}",
        "detail": "Màu nâng cao DarkGrey (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkKhaki}",
        "insertText": "\\color{DarkKhaki}",
        "detail": "Màu nâng cao DarkKhaki (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkMagenta}",
        "insertText": "\\color{DarkMagenta}",
        "detail": "Màu nâng cao DarkMagenta (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkOliveGreen}",
        "insertText": "\\color{DarkOliveGreen}",
        "detail": "Màu nâng cao DarkOliveGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkOrange}",
        "insertText": "\\color{DarkOrange}",
        "detail": "Màu nâng cao DarkOrange (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkOrchid}",
        "insertText": "\\color{DarkOrchid}",
        "detail": "Màu nâng cao DarkOrchid (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkRed}",
        "insertText": "\\color{DarkRed}",
        "detail": "Màu nâng cao DarkRed (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkSalmon}",
        "insertText": "\\color{DarkSalmon}",
        "detail": "Màu nâng cao DarkSalmon (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkSeaGreen}",
        "insertText": "\\color{DarkSeaGreen}",
        "detail": "Màu nâng cao DarkSeaGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkSlateBlue}",
        "insertText": "\\color{DarkSlateBlue}",
        "detail": "Màu nâng cao DarkSlateBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkSlateGray}",
        "insertText": "\\color{DarkSlateGray}",
        "detail": "Màu nâng cao DarkSlateGray (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkSlateGrey}",
        "insertText": "\\color{DarkSlateGrey}",
        "detail": "Màu nâng cao DarkSlateGrey (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkTurquoise}",
        "insertText": "\\color{DarkTurquoise}",
        "detail": "Màu nâng cao DarkTurquoise (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DarkViolet}",
        "insertText": "\\color{DarkViolet}",
        "detail": "Màu nâng cao DarkViolet (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DeepPink}",
        "insertText": "\\color{DeepPink}",
        "detail": "Màu nâng cao DeepPink (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DeepSkyBlue}",
        "insertText": "\\color{DeepSkyBlue}",
        "detail": "Màu nâng cao DeepSkyBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DimGray}",
        "insertText": "\\color{DimGray}",
        "detail": "Màu nâng cao DimGray (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DimGrey}",
        "insertText": "\\color{DimGrey}",
        "detail": "Màu nâng cao DimGrey (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{DodgerBlue}",
        "insertText": "\\color{DodgerBlue}",
        "detail": "Màu nâng cao DodgerBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{FireBrick}",
        "insertText": "\\color{FireBrick}",
        "detail": "Màu nâng cao FireBrick (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{FloralWhite}",
        "insertText": "\\color{FloralWhite}",
        "detail": "Màu nâng cao FloralWhite (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{ForestGreen}",
        "insertText": "\\color{ForestGreen}",
        "detail": "Màu nâng cao ForestGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Fuchsia}",
        "insertText": "\\color{Fuchsia}",
        "detail": "Màu nâng cao Fuchsia (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Gainsboro}",
        "insertText": "\\color{Gainsboro}",
        "detail": "Màu nâng cao Gainsboro (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{GhostWhite}",
        "insertText": "\\color{GhostWhite}",
        "detail": "Màu nâng cao GhostWhite (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Gold}",
        "insertText": "\\color{Gold}",
        "detail": "Màu nâng cao Gold (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Goldenrod}",
        "insertText": "\\color{Goldenrod}",
        "detail": "Màu nâng cao Goldenrod (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Gray}",
        "insertText": "\\color{Gray}",
        "detail": "Màu nâng cao Gray (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Green}",
        "insertText": "\\color{Green}",
        "detail": "Màu nâng cao Green (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{GreenYellow}",
        "insertText": "\\color{GreenYellow}",
        "detail": "Màu nâng cao GreenYellow (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Grey}",
        "insertText": "\\color{Grey}",
        "detail": "Màu nâng cao Grey (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Honeydew}",
        "insertText": "\\color{Honeydew}",
        "detail": "Màu nâng cao Honeydew (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{HotPink}",
        "insertText": "\\color{HotPink}",
        "detail": "Màu nâng cao HotPink (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{IndianRed}",
        "insertText": "\\color{IndianRed}",
        "detail": "Màu nâng cao IndianRed (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Indigo}",
        "insertText": "\\color{Indigo}",
        "detail": "Màu nâng cao Indigo (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Ivory}",
        "insertText": "\\color{Ivory}",
        "detail": "Màu nâng cao Ivory (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Khaki}",
        "insertText": "\\color{Khaki}",
        "detail": "Màu nâng cao Khaki (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Lavender}",
        "insertText": "\\color{Lavender}",
        "detail": "Màu nâng cao Lavender (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LavenderBlush}",
        "insertText": "\\color{LavenderBlush}",
        "detail": "Màu nâng cao LavenderBlush (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LawnGreen}",
        "insertText": "\\color{LawnGreen}",
        "detail": "Màu nâng cao LawnGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LemonChiffon}",
        "insertText": "\\color{LemonChiffon}",
        "detail": "Màu nâng cao LemonChiffon (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightBlue}",
        "insertText": "\\color{LightBlue}",
        "detail": "Màu nâng cao LightBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightCoral}",
        "insertText": "\\color{LightCoral}",
        "detail": "Màu nâng cao LightCoral (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightCyan}",
        "insertText": "\\color{LightCyan}",
        "detail": "Màu nâng cao LightCyan (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightGoldenrod}",
        "insertText": "\\color{LightGoldenrod}",
        "detail": "Màu nâng cao LightGoldenrod (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightGoldenrodYellow}",
        "insertText": "\\color{LightGoldenrodYellow}",
        "detail": "Màu nâng cao LightGoldenrodYellow (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightGray}",
        "insertText": "\\color{LightGray}",
        "detail": "Màu nâng cao LightGray (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightGreen}",
        "insertText": "\\color{LightGreen}",
        "detail": "Màu nâng cao LightGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightGrey}",
        "insertText": "\\color{LightGrey}",
        "detail": "Màu nâng cao LightGrey (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightPink}",
        "insertText": "\\color{LightPink}",
        "detail": "Màu nâng cao LightPink (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightSalmon}",
        "insertText": "\\color{LightSalmon}",
        "detail": "Màu nâng cao LightSalmon (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightSeaGreen}",
        "insertText": "\\color{LightSeaGreen}",
        "detail": "Màu nâng cao LightSeaGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightSkyBlue}",
        "insertText": "\\color{LightSkyBlue}",
        "detail": "Màu nâng cao LightSkyBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightSlateBlue}",
        "insertText": "\\color{LightSlateBlue}",
        "detail": "Màu nâng cao LightSlateBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightSlateGray}",
        "insertText": "\\color{LightSlateGray}",
        "detail": "Màu nâng cao LightSlateGray (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightSlateGrey}",
        "insertText": "\\color{LightSlateGrey}",
        "detail": "Màu nâng cao LightSlateGrey (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightSteelBlue}",
        "insertText": "\\color{LightSteelBlue}",
        "detail": "Màu nâng cao LightSteelBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LightYellow}",
        "insertText": "\\color{LightYellow}",
        "detail": "Màu nâng cao LightYellow (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Lime}",
        "insertText": "\\color{Lime}",
        "detail": "Màu nâng cao Lime (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{LimeGreen}",
        "insertText": "\\color{LimeGreen}",
        "detail": "Màu nâng cao LimeGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Linen}",
        "insertText": "\\color{Linen}",
        "detail": "Màu nâng cao Linen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Magenta}",
        "insertText": "\\color{Magenta}",
        "detail": "Màu nâng cao Magenta (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Maroon}",
        "insertText": "\\color{Maroon}",
        "detail": "Màu nâng cao Maroon (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MediumAquamarine}",
        "insertText": "\\color{MediumAquamarine}",
        "detail": "Màu nâng cao MediumAquamarine (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MediumBlue}",
        "insertText": "\\color{MediumBlue}",
        "detail": "Màu nâng cao MediumBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MediumOrchid}",
        "insertText": "\\color{MediumOrchid}",
        "detail": "Màu nâng cao MediumOrchid (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MediumPurple}",
        "insertText": "\\color{MediumPurple}",
        "detail": "Màu nâng cao MediumPurple (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MediumSeaGreen}",
        "insertText": "\\color{MediumSeaGreen}",
        "detail": "Màu nâng cao MediumSeaGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MediumSlateBlue}",
        "insertText": "\\color{MediumSlateBlue}",
        "detail": "Màu nâng cao MediumSlateBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MediumSpringGreen}",
        "insertText": "\\color{MediumSpringGreen}",
        "detail": "Màu nâng cao MediumSpringGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MediumTurquoise}",
        "insertText": "\\color{MediumTurquoise}",
        "detail": "Màu nâng cao MediumTurquoise (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MediumVioletRed}",
        "insertText": "\\color{MediumVioletRed}",
        "detail": "Màu nâng cao MediumVioletRed (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MidnightBlue}",
        "insertText": "\\color{MidnightBlue}",
        "detail": "Màu nâng cao MidnightBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MintCream}",
        "insertText": "\\color{MintCream}",
        "detail": "Màu nâng cao MintCream (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{MistyRose}",
        "insertText": "\\color{MistyRose}",
        "detail": "Màu nâng cao MistyRose (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Moccasin}",
        "insertText": "\\color{Moccasin}",
        "detail": "Màu nâng cao Moccasin (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{NavajoWhite}",
        "insertText": "\\color{NavajoWhite}",
        "detail": "Màu nâng cao NavajoWhite (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Navy}",
        "insertText": "\\color{Navy}",
        "detail": "Màu nâng cao Navy (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{NavyBlue}",
        "insertText": "\\color{NavyBlue}",
        "detail": "Màu nâng cao NavyBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{OldLace}",
        "insertText": "\\color{OldLace}",
        "detail": "Màu nâng cao OldLace (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Olive}",
        "insertText": "\\color{Olive}",
        "detail": "Màu nâng cao Olive (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{OliveDrab}",
        "insertText": "\\color{OliveDrab}",
        "detail": "Màu nâng cao OliveDrab (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Orange}",
        "insertText": "\\color{Orange}",
        "detail": "Màu nâng cao Orange (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{OrangeRed}",
        "insertText": "\\color{OrangeRed}",
        "detail": "Màu nâng cao OrangeRed (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Orchid}",
        "insertText": "\\color{Orchid}",
        "detail": "Màu nâng cao Orchid (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{PaleGoldenrod}",
        "insertText": "\\color{PaleGoldenrod}",
        "detail": "Màu nâng cao PaleGoldenrod (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{PaleGreen}",
        "insertText": "\\color{PaleGreen}",
        "detail": "Màu nâng cao PaleGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{PaleTurquoise}",
        "insertText": "\\color{PaleTurquoise}",
        "detail": "Màu nâng cao PaleTurquoise (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{PaleVioletRed}",
        "insertText": "\\color{PaleVioletRed}",
        "detail": "Màu nâng cao PaleVioletRed (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{PapayaWhip}",
        "insertText": "\\color{PapayaWhip}",
        "detail": "Màu nâng cao PapayaWhip (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{PeachPuff}",
        "insertText": "\\color{PeachPuff}",
        "detail": "Màu nâng cao PeachPuff (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Peru}",
        "insertText": "\\color{Peru}",
        "detail": "Màu nâng cao Peru (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Pink}",
        "insertText": "\\color{Pink}",
        "detail": "Màu nâng cao Pink (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Plum}",
        "insertText": "\\color{Plum}",
        "detail": "Màu nâng cao Plum (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{PowderBlue}",
        "insertText": "\\color{PowderBlue}",
        "detail": "Màu nâng cao PowderBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Purple}",
        "insertText": "\\color{Purple}",
        "detail": "Màu nâng cao Purple (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Red}",
        "insertText": "\\color{Red}",
        "detail": "Màu nâng cao Red (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{RosyBrown}",
        "insertText": "\\color{RosyBrown}",
        "detail": "Màu nâng cao RosyBrown (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{RoyalBlue}",
        "insertText": "\\color{RoyalBlue}",
        "detail": "Màu nâng cao RoyalBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SaddleBrown}",
        "insertText": "\\color{SaddleBrown}",
        "detail": "Màu nâng cao SaddleBrown (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Salmon}",
        "insertText": "\\color{Salmon}",
        "detail": "Màu nâng cao Salmon (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SandyBrown}",
        "insertText": "\\color{SandyBrown}",
        "detail": "Màu nâng cao SandyBrown (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SeaGreen}",
        "insertText": "\\color{SeaGreen}",
        "detail": "Màu nâng cao SeaGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SeaShell}",
        "insertText": "\\color{SeaShell}",
        "detail": "Màu nâng cao SeaShell (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Sienna}",
        "insertText": "\\color{Sienna}",
        "detail": "Màu nâng cao Sienna (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Silver}",
        "insertText": "\\color{Silver}",
        "detail": "Màu nâng cao Silver (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SkyBlue}",
        "insertText": "\\color{SkyBlue}",
        "detail": "Màu nâng cao SkyBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SlateBlue}",
        "insertText": "\\color{SlateBlue}",
        "detail": "Màu nâng cao SlateBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SlateGray}",
        "insertText": "\\color{SlateGray}",
        "detail": "Màu nâng cao SlateGray (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SlateGrey}",
        "insertText": "\\color{SlateGrey}",
        "detail": "Màu nâng cao SlateGrey (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Snow}",
        "insertText": "\\color{Snow}",
        "detail": "Màu nâng cao Snow (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SpringGreen}",
        "insertText": "\\color{SpringGreen}",
        "detail": "Màu nâng cao SpringGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{SteelBlue}",
        "insertText": "\\color{SteelBlue}",
        "detail": "Màu nâng cao SteelBlue (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Tan}",
        "insertText": "\\color{Tan}",
        "detail": "Màu nâng cao Tan (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Teal}",
        "insertText": "\\color{Teal}",
        "detail": "Màu nâng cao Teal (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Thistle}",
        "insertText": "\\color{Thistle}",
        "detail": "Màu nâng cao Thistle (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Tomato}",
        "insertText": "\\color{Tomato}",
        "detail": "Màu nâng cao Tomato (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Turquoise}",
        "insertText": "\\color{Turquoise}",
        "detail": "Màu nâng cao Turquoise (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Violet}",
        "insertText": "\\color{Violet}",
        "detail": "Màu nâng cao Violet (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{VioletRed}",
        "insertText": "\\color{VioletRed}",
        "detail": "Màu nâng cao VioletRed (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Wheat}",
        "insertText": "\\color{Wheat}",
        "detail": "Màu nâng cao Wheat (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{White}",
        "insertText": "\\color{White}",
        "detail": "Màu nâng cao White (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{WhiteSmoke}",
        "insertText": "\\color{WhiteSmoke}",
        "detail": "Màu nâng cao WhiteSmoke (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{Yellow}",
        "insertText": "\\color{Yellow}",
        "detail": "Màu nâng cao Yellow (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\color{YellowGreen}",
        "insertText": "\\color{YellowGreen}",
        "detail": "Màu nâng cao YellowGreen (svgnames)",
        "type": "snippet"
    },
    {
        "label": "\\textdegree",
        "insertText": "\\textdegree",
        "detail": "Ký hiệu văn bản textdegree",
        "type": "snippet"
    },
    {
        "label": "\\textcelsius",
        "insertText": "\\textcelsius",
        "detail": "Ký hiệu văn bản textcelsius",
        "type": "snippet"
    },
    {
        "label": "\\textbullet",
        "insertText": "\\textbullet",
        "detail": "Ký hiệu văn bản textbullet",
        "type": "snippet"
    },
    {
        "label": "\\textcopyright",
        "insertText": "\\textcopyright",
        "detail": "Ký hiệu văn bản textcopyright",
        "type": "snippet"
    },
    {
        "label": "\\texteuro",
        "insertText": "\\texteuro",
        "detail": "Ký hiệu văn bản texteuro",
        "type": "snippet"
    },
    {
        "label": "\\textyen",
        "insertText": "\\textyen",
        "detail": "Ký hiệu văn bản textyen",
        "type": "snippet"
    },
    {
        "label": "\\textsterling",
        "insertText": "\\textsterling",
        "detail": "Ký hiệu văn bản textsterling",
        "type": "snippet"
    },
    {
        "label": "\\textwon",
        "insertText": "\\textwon",
        "detail": "Ký hiệu văn bản textwon",
        "type": "snippet"
    },
    {
        "label": "\\textnaira",
        "insertText": "\\textnaira",
        "detail": "Ký hiệu văn bản textnaira",
        "type": "snippet"
    },
    {
        "label": "\\textpeso",
        "insertText": "\\textpeso",
        "detail": "Ký hiệu văn bản textpeso",
        "type": "snippet"
    },
    {
        "label": "\\textlira",
        "insertText": "\\textlira",
        "detail": "Ký hiệu văn bản textlira",
        "type": "snippet"
    },
    {
        "label": "\\textrecipe",
        "insertText": "\\textrecipe",
        "detail": "Ký hiệu văn bản textrecipe",
        "type": "snippet"
    },
    {
        "label": "\\textdiscount",
        "insertText": "\\textdiscount",
        "detail": "Ký hiệu văn bản textdiscount",
        "type": "snippet"
    },
    {
        "label": "\\textestimated",
        "insertText": "\\textestimated",
        "detail": "Ký hiệu văn bản textestimated",
        "type": "snippet"
    },
    {
        "label": "\\textpertenthousand",
        "insertText": "\\textpertenthousand",
        "detail": "Ký hiệu văn bản textpertenthousand",
        "type": "snippet"
    },
    {
        "label": "\\textperthousand",
        "insertText": "\\textperthousand",
        "detail": "Ký hiệu văn bản textperthousand",
        "type": "snippet"
    },
    {
        "label": "\\textmu",
        "insertText": "\\textmu",
        "detail": "Ký hiệu văn bản textmu",
        "type": "snippet"
    },
    {
        "label": "\\textohm",
        "insertText": "\\textohm",
        "detail": "Ký hiệu văn bản textohm",
        "type": "snippet"
    },
    {
        "label": "\\textmho",
        "insertText": "\\textmho",
        "detail": "Ký hiệu văn bản textmho",
        "type": "snippet"
    },
    {
        "label": "\\textasciitilde",
        "insertText": "\\textasciitilde",
        "detail": "Ký hiệu văn bản textasciitilde",
        "type": "snippet"
    },
    {
        "label": "\\textasciicircum",
        "insertText": "\\textasciicircum",
        "detail": "Ký hiệu văn bản textasciicircum",
        "type": "snippet"
    },
    {
        "label": "\\textbackslash",
        "insertText": "\\textbackslash",
        "detail": "Ký hiệu văn bản textbackslash",
        "type": "snippet"
    },
    {
        "label": "\\textbar",
        "insertText": "\\textbar",
        "detail": "Ký hiệu văn bản textbar",
        "type": "snippet"
    },
    {
        "label": "\\textless",
        "insertText": "\\textless",
        "detail": "Ký hiệu văn bản textless",
        "type": "snippet"
    },
    {
        "label": "\\textgCreater",
        "insertText": "\\textgCreater",
        "detail": "Ký hiệu văn bản textgCreater",
        "type": "snippet"
    },
    {
        "label": "\\textbraceleft",
        "insertText": "\\textbraceleft",
        "detail": "Ký hiệu văn bản textbraceleft",
        "type": "snippet"
    },
    {
        "label": "\\textbraceright",
        "insertText": "\\textbraceright",
        "detail": "Ký hiệu văn bản textbraceright",
        "type": "snippet"
    },
    {
        "label": "\\textendash",
        "insertText": "\\textendash",
        "detail": "Ký hiệu văn bản textendash",
        "type": "snippet"
    },
    {
        "label": "\\textemdash",
        "insertText": "\\textemdash",
        "detail": "Ký hiệu văn bản textemdash",
        "type": "snippet"
    },
    {
        "label": "\\textquoteleft",
        "insertText": "\\textquoteleft",
        "detail": "Ký hiệu văn bản textquoteleft",
        "type": "snippet"
    },
    {
        "label": "\\textquoteright",
        "insertText": "\\textquoteright",
        "detail": "Ký hiệu văn bản textquoteright",
        "type": "snippet"
    },
    {
        "label": "\\textquotedblleft",
        "insertText": "\\textquotedblleft",
        "detail": "Ký hiệu văn bản textquotedblleft",
        "type": "snippet"
    },
    {
        "label": "\\textquotedblright",
        "insertText": "\\textquotedblright",
        "detail": "Ký hiệu văn bản textquotedblright",
        "type": "snippet"
    },
    {
        "label": "\\textunderscore",
        "insertText": "\\textunderscore",
        "detail": "Ký hiệu văn bản textunderscore",
        "type": "snippet"
    },
    {
        "label": "\\addplot coordinates arg1",
        "insertText": "\\addplot coordinates ${1:arg1}",
        "detail": "Thêm giá trị từ tọa độ",
        "type": "snippet"
    },
    {
        "label": "\\addplot table arg1",
        "insertText": "\\addplot table ${1:arg1}",
        "detail": "Thêm giá trị từ bảng",
        "type": "snippet"
    },
    {
        "label": "\\addplot expression arg1",
        "insertText": "\\addplot expression ${1:arg1}",
        "detail": "Thêm giá trị hàm số",
        "type": "snippet"
    },
    {
        "label": "\\addplot3",
        "insertText": "\\addplot3",
        "detail": "Thêm giá trị 3D",
        "type": "snippet"
    },
    {
        "label": "\\addlegendentry{arg1}",
        "insertText": "\\addlegendentry{${1:arg1}}",
        "detail": "Chú thích biểu đồ",
        "type": "snippet"
    },
    {
        "label": "\\If",
        "insertText": "\\If",
        "detail": "Lệnh thuật toán If",
        "type": "snippet"
    },
    {
        "label": "\\ElseIf",
        "insertText": "\\ElseIf",
        "detail": "Lệnh thuật toán ElseIf",
        "type": "snippet"
    },
    {
        "label": "\\Else",
        "insertText": "\\Else",
        "detail": "Lệnh thuật toán Else",
        "type": "snippet"
    },
    {
        "label": "\\EndIf",
        "insertText": "\\EndIf",
        "detail": "Lệnh thuật toán EndIf",
        "type": "snippet"
    },
    {
        "label": "\\For",
        "insertText": "\\For",
        "detail": "Lệnh thuật toán For",
        "type": "snippet"
    },
    {
        "label": "\\ForAll",
        "insertText": "\\ForAll",
        "detail": "Lệnh thuật toán ForAll",
        "type": "snippet"
    },
    {
        "label": "\\EndFor",
        "insertText": "\\EndFor",
        "detail": "Lệnh thuật toán EndFor",
        "type": "snippet"
    },
    {
        "label": "\\While",
        "insertText": "\\While",
        "detail": "Lệnh thuật toán While",
        "type": "snippet"
    },
    {
        "label": "\\EndWhile",
        "insertText": "\\EndWhile",
        "detail": "Lệnh thuật toán EndWhile",
        "type": "snippet"
    },
    {
        "label": "\\Repeat",
        "insertText": "\\Repeat",
        "detail": "Lệnh thuật toán Repeat",
        "type": "snippet"
    },
    {
        "label": "\\Until",
        "insertText": "\\Until",
        "detail": "Lệnh thuật toán Until",
        "type": "snippet"
    },
    {
        "label": "\\Loop",
        "insertText": "\\Loop",
        "detail": "Lệnh thuật toán Loop",
        "type": "snippet"
    },
    {
        "label": "\\EndLoop",
        "insertText": "\\EndLoop",
        "detail": "Lệnh thuật toán EndLoop",
        "type": "snippet"
    },
    {
        "label": "\\Require",
        "insertText": "\\Require",
        "detail": "Lệnh thuật toán Require",
        "type": "snippet"
    },
    {
        "label": "\\Ensure",
        "insertText": "\\Ensure",
        "detail": "Lệnh thuật toán Ensure",
        "type": "snippet"
    },
    {
        "label": "\\Print",
        "insertText": "\\Print",
        "detail": "Lệnh thuật toán Print",
        "type": "snippet"
    },
    {
        "label": "\\KwIn{arg1}",
        "insertText": "\\KwIn{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) KwIn",
        "type": "snippet"
    },
    {
        "label": "\\KwOut{arg1}",
        "insertText": "\\KwOut{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) KwOut",
        "type": "snippet"
    },
    {
        "label": "\\KwData{arg1}",
        "insertText": "\\KwData{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) KwData",
        "type": "snippet"
    },
    {
        "label": "\\KwResult{arg1}",
        "insertText": "\\KwResult{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) KwResult",
        "type": "snippet"
    },
    {
        "label": "\\tcp{arg1}",
        "insertText": "\\tcp{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) tcp",
        "type": "snippet"
    },
    {
        "label": "\\tcc{arg1}",
        "insertText": "\\tcc{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) tcc",
        "type": "snippet"
    },
    {
        "label": "\\uIf{arg1}",
        "insertText": "\\uIf{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) uIf",
        "type": "snippet"
    },
    {
        "label": "\\lIf{arg1}",
        "insertText": "\\lIf{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) lIf",
        "type": "snippet"
    },
    {
        "label": "\\uElseIf{arg1}",
        "insertText": "\\uElseIf{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) uElseIf",
        "type": "snippet"
    },
    {
        "label": "\\lElseIf{arg1}",
        "insertText": "\\lElseIf{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) lElseIf",
        "type": "snippet"
    },
    {
        "label": "\\uElse{arg1}",
        "insertText": "\\uElse{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) uElse",
        "type": "snippet"
    },
    {
        "label": "\\lElse{arg1}",
        "insertText": "\\lElse{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) lElse",
        "type": "snippet"
    },
    {
        "label": "\\uFor{arg1}",
        "insertText": "\\uFor{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) uFor",
        "type": "snippet"
    },
    {
        "label": "\\lFor{arg1}",
        "insertText": "\\lFor{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) lFor",
        "type": "snippet"
    },
    {
        "label": "\\uWhile{arg1}",
        "insertText": "\\uWhile{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) uWhile",
        "type": "snippet"
    },
    {
        "label": "\\lWhile{arg1}",
        "insertText": "\\lWhile{${1:arg1}}",
        "detail": "Thuật toán (Algorithm2e) lWhile",
        "type": "snippet"
    },
    {
        "label": "\\addbibresource{arg1}",
        "insertText": "\\addbibresource{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) addbibresource",
        "type": "snippet"
    },
    {
        "label": "\\printbibliography{arg1}",
        "insertText": "\\printbibliography{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) printbibliography",
        "type": "snippet"
    },
    {
        "label": "\\autocite{arg1}",
        "insertText": "\\autocite{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) autocite",
        "type": "snippet"
    },
    {
        "label": "\\textcite{arg1}",
        "insertText": "\\textcite{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) textcite",
        "type": "snippet"
    },
    {
        "label": "\\parencite{arg1}",
        "insertText": "\\parencite{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) parencite",
        "type": "snippet"
    },
    {
        "label": "\\footcite{arg1}",
        "insertText": "\\footcite{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) footcite",
        "type": "snippet"
    },
    {
        "label": "\\fullcite{arg1}",
        "insertText": "\\fullcite{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) fullcite",
        "type": "snippet"
    },
    {
        "label": "\\citeauthor{arg1}",
        "insertText": "\\citeauthor{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) citeauthor",
        "type": "snippet"
    },
    {
        "label": "\\citetitle{arg1}",
        "insertText": "\\citetitle{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) citetitle",
        "type": "snippet"
    },
    {
        "label": "\\citeyear{arg1}",
        "insertText": "\\citeyear{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) citeyear",
        "type": "snippet"
    },
    {
        "label": "\\citenum{arg1}",
        "insertText": "\\citenum{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) citenum",
        "type": "snippet"
    },
    {
        "label": "\\supercite{arg1}",
        "insertText": "\\supercite{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) supercite",
        "type": "snippet"
    },
    {
        "label": "\\nocite{arg1}",
        "insertText": "\\nocite{${1:arg1}}",
        "detail": "Thư mục (BibLaTeX) nocite",
        "type": "snippet"
    },
    {
        "label": "\\crefrange{arg1}",
        "insertText": "\\crefrange{${1:arg1}}",
        "detail": "Tham chiếu thông minh crefrange",
        "type": "snippet"
    },
    {
        "label": "\\Crefrange{arg1}",
        "insertText": "\\Crefrange{${1:arg1}}",
        "detail": "Tham chiếu thông minh Crefrange",
        "type": "snippet"
    },
    {
        "label": "\\tcbset{arg1}",
        "insertText": "\\tcbset{${1:arg1}}",
        "detail": "Tùy chỉnh tcolorbox",
        "type": "snippet"
    },
    {
        "label": "\\lstinline| |",
        "insertText": "\\lstinline| |",
        "detail": "Mã inline",
        "type": "snippet"
    },
    {
        "label": "\\lstset{arg1}",
        "insertText": "\\lstset{${1:arg1}}",
        "detail": "Cấu hình listings",
        "type": "snippet"
    },
    {
        "label": "\\lstinputlisting{arg1}",
        "insertText": "\\lstinputlisting{${1:arg1}}",
        "detail": "Đọc mã từ file",
        "type": "snippet"
    },
    {
        "label": "\\`arg1",
        "insertText": "\\`${1:arg1}",
        "detail": "Dấu phụ dấu huyền",
        "type": "snippet"
    },
    {
        "label": "\\'arg1",
        "insertText": "\\'${1:arg1}",
        "detail": "Dấu phụ dấu sắc",
        "type": "snippet"
    },
    {
        "label": "\\^arg1",
        "insertText": "\\^${1:arg1}",
        "detail": "Dấu phụ dấu mũ",
        "type": "snippet"
    },
    {
        "label": "\\\"arg1",
        "insertText": "\\\"${1:arg1}",
        "detail": "Dấu phụ dấu diaeresis",
        "type": "snippet"
    },
    {
        "label": "\\~arg1",
        "insertText": "\\~${1:arg1}",
        "detail": "Dấu phụ dấu ngã",
        "type": "snippet"
    },
    {
        "label": "\\=arg1",
        "insertText": "\\=${1:arg1}",
        "detail": "Dấu phụ dấu gạch ngang (macron)",
        "type": "snippet"
    },
    {
        "label": "\\.arg1",
        "insertText": "\\.${1:arg1}",
        "detail": "Dấu phụ dấu chấm (dot)",
        "type": "snippet"
    },
    {
        "label": "\\u{arg1}",
        "insertText": "\\u{${1:arg1}}",
        "detail": "Dấu phụ dấu breve",
        "type": "snippet"
    },
    {
        "label": "\\v{arg1}",
        "insertText": "\\v{${1:arg1}}",
        "detail": "Dấu phụ dấu caron",
        "type": "snippet"
    },
    {
        "label": "\\H{arg1}",
        "insertText": "\\H{${1:arg1}}",
        "detail": "Dấu phụ dấu double acute",
        "type": "snippet"
    },
    {
        "label": "\\t{arg1}",
        "insertText": "\\t{${1:arg1}}",
        "detail": "Dấu phụ dấu tie",
        "type": "snippet"
    },
    {
        "label": "\\c{arg1}",
        "insertText": "\\c{${1:arg1}}",
        "detail": "Dấu phụ dấu cedilla",
        "type": "snippet"
    },
    {
        "label": "\\d{arg1}",
        "insertText": "\\d{${1:arg1}}",
        "detail": "Dấu phụ dấu chấm dưới",
        "type": "snippet"
    },
    {
        "label": "\\b{arg1}",
        "insertText": "\\b{${1:arg1}}",
        "detail": "Dấu phụ dấu gạch chân dính",
        "type": "snippet"
    },
    {
        "label": "\\newcounter{arg1}",
        "insertText": "\\newcounter{${1:arg1}}",
        "detail": "Biến đếm newcounter",
        "type": "snippet"
    },
    {
        "label": "\\addtocounter{arg1}",
        "insertText": "\\addtocounter{${1:arg1}}",
        "detail": "Biến đếm addtocounter",
        "type": "snippet"
    },
    {
        "label": "\\stepcounter{arg1}",
        "insertText": "\\stepcounter{${1:arg1}}",
        "detail": "Biến đếm stepcounter",
        "type": "snippet"
    },
    {
        "label": "\\refstepcounter{arg1}",
        "insertText": "\\refstepcounter{${1:arg1}}",
        "detail": "Biến đếm refstepcounter",
        "type": "snippet"
    },
    {
        "label": "\\value{arg1}",
        "insertText": "\\value{${1:arg1}}",
        "detail": "Biến đếm value",
        "type": "snippet"
    },
    {
        "label": "\\fnsymbol{arg1}",
        "insertText": "\\fnsymbol{${1:arg1}}",
        "detail": "Biến đếm fnsymbol",
        "type": "snippet"
    },
    {
        "label": "\\RequirePackage",
        "insertText": "\\RequirePackage",
        "detail": "Yêu cầu gói (thường dùng trong viết Class/Style)",
        "type": "snippet"
    },
    {
        "label": "\\ProvidesPackage",
        "insertText": "\\ProvidesPackage",
        "detail": "Cung cấp tên cấu trúc cho một gói",
        "type": "snippet"
    },
    {
        "label": "\\ProvidesClass",
        "insertText": "\\ProvidesClass",
        "detail": "Cung cấp tên cho lớp tài liệu",
        "type": "snippet"
    },
    {
        "label": "\\DeclareRobustCommand",
        "insertText": "\\DeclareRobustCommand",
        "detail": "Khai báo lệnh một cách an toàn (Robust)",
        "type": "snippet"
    },
    {
        "label": "\\numberwithin",
        "insertText": "\\numberwithin",
        "detail": "Đánh số công thức theo chương/mục",
        "type": "snippet"
    },
    {
        "label": "\\settowidth",
        "insertText": "\\settowidth",
        "detail": "Gán độ dài bằng với chiều rộng của chuỗi",
        "type": "snippet"
    },
    {
        "label": "\\settoheight",
        "insertText": "\\settoheight",
        "detail": "Gán độ dài bằng với chiều cao của chuỗi",
        "type": "snippet"
    },
    {
        "label": "\\settodepth",
        "insertText": "\\settodepth",
        "detail": "Gán độ dài bằng với chiều sâu của chuỗi",
        "type": "snippet"
    },
    {
        "label": "\\phantom",
        "insertText": "\\phantom",
        "detail": "Tạo ô trống ảo có kích thước bằng chuỗi ký tự",
        "type": "snippet"
    },
    {
        "label": "\\hphantom",
        "insertText": "\\hphantom",
        "detail": "Tạo ô trống ngang ảo",
        "type": "snippet"
    },
    {
        "label": "\\vphantom",
        "insertText": "\\vphantom",
        "detail": "Tạo ô trống dọc ảo",
        "type": "snippet"
    },
    {
        "label": "\\noindent",
        "insertText": "\\noindent",
        "detail": "Xóa thụt lề dòng đầu tiên",
        "type": "snippet"
    },
    {
        "label": "\\indent",
        "insertText": "\\indent",
        "detail": "Bắt buộc thụt lề dòng",
        "type": "snippet"
    },
    {
        "label": "\\frenchspacing",
        "insertText": "\\frenchspacing",
        "detail": "Khoảng cách sau dấu chấm y hệt dấu cách thường",
        "type": "snippet"
    },
    {
        "label": "\\nonfrenchspacing",
        "insertText": "\\nonfrenchspacing",
        "detail": "Khoảng cách rộng hơn sau dấu chấm câu",
        "type": "snippet"
    },
    {
        "label": "\\sloppy",
        "insertText": "\\sloppy",
        "detail": "Cho phép khoảng đệm chữ giãn rộng (tránh tràn lề)",
        "type": "snippet"
    },
    {
        "label": "\\fussy",
        "insertText": "\\fussy",
        "detail": "Văn bản chặt chẽ (mặc định)",
        "type": "snippet"
    },
    {
        "label": "\\obeylines",
        "insertText": "\\obeylines",
        "detail": "Ép LaTeX tôn trọng ngắt dòng trong source code",
        "type": "snippet"
    },
    {
        "label": "\\obeyspaces",
        "insertText": "\\obeyspaces",
        "detail": "Ép LaTeX tôn trọng khoảng trắng liên tiếp",
        "type": "snippet"
    },
    {
        "label": "\\boxdot",
        "insertText": "\\boxdot",
        "detail": "Hình hộp có dấu chấm",
        "type": "snippet"
    },
    {
        "label": "\\lozenge",
        "insertText": "\\lozenge",
        "detail": "Hình thoi rỗng",
        "type": "snippet"
    },
    {
        "label": "\\blacklozenge",
        "insertText": "\\blacklozenge",
        "detail": "Hình thoi đặc đen",
        "type": "snippet"
    },
    {
        "label": "\\circlearrowleft",
        "insertText": "\\circlearrowleft",
        "detail": "Mũi tên vòng sang trái",
        "type": "snippet"
    },
    {
        "label": "\\circlearrowright",
        "insertText": "\\circlearrowright",
        "detail": "Mũi tên vòng sang phải",
        "type": "snippet"
    },
    {
        "label": "\\intercal",
        "insertText": "\\intercal",
        "detail": "Phép chuyển vị / xen kẽ",
        "type": "snippet"
    },
    {
        "label": "\\divideontimes",
        "insertText": "\\divideontimes",
        "detail": "Phép chia có chéo nhân",
        "type": "snippet"
    },
    {
        "label": "\\subseteqq",
        "insertText": "\\subseteqq",
        "detail": "Tập con với nét gạch ngang kép",
        "type": "snippet"
    },
    {
        "label": "\\supseteqq",
        "insertText": "\\supseteqq",
        "detail": "Tập chứa với nét gạch ngang kép",
        "type": "snippet"
    },
    {
        "label": "\\ntriangleleft",
        "insertText": "\\ntriangleleft",
        "detail": "Không là tam giác trái",
        "type": "snippet"
    },
    {
        "label": "\\ntriangleright",
        "insertText": "\\ntriangleright",
        "detail": "Không là tam giác phải",
        "type": "snippet"
    },
    {
        "label": "\\nsupseteq",
        "insertText": "\\nsupseteq",
        "detail": "Không là tập chứa",
        "type": "snippet"
    },
    {
        "label": "\\autoref",
        "insertText": "\\autoref",
        "detail": "Tham chiếu tự động đính kèm loại (Hình, Bảng...)",
        "type": "snippet"
    },
    {
        "label": "\\pagestyle",
        "insertText": "\\pagestyle",
        "detail": "Định dạng kiểu Header/Footer cho toàn văn bản",
        "type": "snippet"
    },
    {
        "label": "\\thispagestyle",
        "insertText": "\\thispagestyle",
        "detail": "Trang trí Header/Footer riêng trang hiện tại",
        "type": "snippet"
    },
    {
        "label": "\\fancyhf",
        "insertText": "\\fancyhf",
        "detail": "Xóa toàn bộ Header/Footer của gói fancyhdr",
        "type": "snippet"
    },
    {
        "label": "\\fancyhead",
        "insertText": "\\fancyhead",
        "detail": "Cài đặt nội dung Header (fancyhdr)",
        "type": "snippet"
    },
    {
        "label": "\\fancyfoot",
        "insertText": "\\fancyfoot",
        "detail": "Cài đặt nội dung Footer (fancyhdr)",
        "type": "snippet"
    },
    {
        "label": "\\lhead",
        "insertText": "\\lhead",
        "detail": "Nội dung Header góc trái",
        "type": "snippet"
    },
    {
        "label": "\\chead",
        "insertText": "\\chead",
        "detail": "Nội dung Header ở giữa",
        "type": "snippet"
    },
    {
        "label": "\\rhead",
        "insertText": "\\rhead",
        "detail": "Nội dung Header góc phải",
        "type": "snippet"
    },
    {
        "label": "\\lfoot",
        "insertText": "\\lfoot",
        "detail": "Nội dung Footer góc trái",
        "type": "snippet"
    },
    {
        "label": "\\cfoot",
        "insertText": "\\cfoot",
        "detail": "Nội dung Footer ở giữa",
        "type": "snippet"
    },
    {
        "label": "\\rfoot",
        "insertText": "\\rfoot",
        "detail": "Nội dung Footer góc phải",
        "type": "snippet"
    },
    {
        "label": "\\only<>",
        "insertText": "\\only<${1:overlay_spec}>{${2:text}}",
        "detail": "Duy nhất trên slide hiện tại (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\uncover<>",
        "insertText": "\\uncover<${1:overlay_spec}>{${2:text}}",
        "detail": "Hiển thị trên slide, ẩn trước đó (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\visible<>",
        "insertText": "\\visible<${1:overlay_spec}>{${2:text}}",
        "detail": "Giống uncover nhưng giữ không gian (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\invisible<>",
        "insertText": "\\invisible<${1:overlay_spec}>{${2:text}}",
        "detail": "Tàng hình nhưng giữ không gian (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\alt<>",
        "insertText": "\\alt<${1:overlay_spec}>{${2:text}}",
        "detail": "Hiển thị văn bản thay thế (Overlay) (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\temporal<>",
        "insertText": "\\temporal<${1:overlay_spec}>{${2:text}}",
        "detail": "Văn bản trước, trong và sau (Overlay) (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\transblindshorizontal<>",
        "insertText": "\\transblindshorizontal<${1:overlay_spec}>{${2:text}}",
        "detail": "Chuyển cảnh mành ngang (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\transblindsvertical<>",
        "insertText": "\\transblindsvertical<${1:overlay_spec}>{${2:text}}",
        "detail": "Chuyển cảnh mành dọc (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\transboxin<>",
        "insertText": "\\transboxin<${1:overlay_spec}>{${2:text}}",
        "detail": "Chuyển cảnh hộp thu hẹp (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\transboxout<>",
        "insertText": "\\transboxout<${1:overlay_spec}>{${2:text}}",
        "detail": "Chuyển cảnh hộp mở rộng (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\transdissolve<>",
        "insertText": "\\transdissolve<${1:overlay_spec}>{${2:text}}",
        "detail": "Chuyển cảnh mờ dần (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\transglitter<>",
        "insertText": "\\transglitter<${1:overlay_spec}>{${2:text}}",
        "detail": "Chuyển cảnh lấp lánh (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\transwipe<>",
        "insertText": "\\transwipe<${1:overlay_spec}>{${2:text}}",
        "detail": "Chuyển cảnh vuốt màn hình (Beamer)",
        "type": "snippet"
    },
    {
        "label": "\\shade[]",
        "insertText": "\\shade[${1:options}] ${2:path};",
        "detail": "Tô đa sắc (Gradient) (TikZ)",
        "type": "snippet"
    },
    {
        "label": "\\shadedraw[]",
        "insertText": "\\shadedraw[${1:options}] ${2:path};",
        "detail": "Vẽ viền và tô đa sắc (TikZ)",
        "type": "snippet"
    },
    {
        "label": "\\useasboundingbox[]",
        "insertText": "\\useasboundingbox[${1:options}] ${2:path};",
        "detail": "Thiết lập khung giới hạn vẽ (TikZ)",
        "type": "snippet"
    },
    {
        "label": "\\pgfmathsetmacro[]",
        "insertText": "\\pgfmathsetmacro[${1:options}] ${2:path};",
        "detail": "Định nghĩa biến toán học PGF (TikZ)",
        "type": "snippet"
    },
    {
        "label": "\\pgfmathparse[]",
        "insertText": "\\pgfmathparse[${1:options}] ${2:path};",
        "detail": "Tính toán giá trị PGF (TikZ)",
        "type": "snippet"
    },
    {
        "label": "\\pgfmathresult[]",
        "insertText": "\\pgfmathresult[${1:options}] ${2:path};",
        "detail": "Kết quả tính toán PGF (TikZ)",
        "type": "snippet"
    },
    {
        "label": "\\arc",
        "insertText": "\\arc[start angle=${1:0}, end angle=${2:90}, radius=${3:1cm}];",
        "detail": "Vẽ cung tròn (TikZ)",
        "type": "snippet"
    },
    {
        "label": "\\parabola",
        "insertText": "\\parabola[${1:options}] (${2:x1},${3:y1}) bend (${4:x2},${5:y2}) (${6:x3},${7:y3});",
        "detail": "Vẽ Parabol (TikZ)",
        "type": "snippet"
    },
    {
        "label": "\\digamma",
        "insertText": "\\digamma",
        "detail": "Ký tự Hy Lạp digamma",
        "type": "snippet"
    },
    {
        "label": "\\varkappa",
        "insertText": "\\varkappa",
        "detail": "Ký tự Hy Lạp varkappa",
        "type": "snippet"
    },
    {
        "label": "\\varGamma",
        "insertText": "\\varGamma",
        "detail": "Ký tự Hy Lạp varGamma",
        "type": "snippet"
    },
    {
        "label": "\\varDelta",
        "insertText": "\\varDelta",
        "detail": "Ký tự Hy Lạp varDelta",
        "type": "snippet"
    },
    {
        "label": "\\varTheta",
        "insertText": "\\varTheta",
        "detail": "Ký tự Hy Lạp varTheta",
        "type": "snippet"
    },
    {
        "label": "\\varLambda",
        "insertText": "\\varLambda",
        "detail": "Ký tự Hy Lạp varLambda",
        "type": "snippet"
    },
    {
        "label": "\\varXi",
        "insertText": "\\varXi",
        "detail": "Ký tự Hy Lạp varXi",
        "type": "snippet"
    },
    {
        "label": "\\varPi",
        "insertText": "\\varPi",
        "detail": "Ký tự Hy Lạp varPi",
        "type": "snippet"
    },
    {
        "label": "\\varSigma",
        "insertText": "\\varSigma",
        "detail": "Ký tự Hy Lạp varSigma",
        "type": "snippet"
    },
    {
        "label": "\\varUpsilon",
        "insertText": "\\varUpsilon",
        "detail": "Ký tự Hy Lạp varUpsilon",
        "type": "snippet"
    },
    {
        "label": "\\varPhi",
        "insertText": "\\varPhi",
        "detail": "Ký tự Hy Lạp varPhi",
        "type": "snippet"
    },
    {
        "label": "\\varPsi",
        "insertText": "\\varPsi",
        "detail": "Ký tự Hy Lạp varPsi",
        "type": "snippet"
    },
    {
        "label": "\\varOmega",
        "insertText": "\\varOmega",
        "detail": "Ký tự Hy Lạp varOmega",
        "type": "snippet"
    },
    {
        "label": "\\ltimes",
        "insertText": "\\ltimes",
        "detail": "Phép nhân trái (Toán)",
        "type": "snippet"
    },
    {
        "label": "\\rtimes",
        "insertText": "\\rtimes",
        "detail": "Phép nhân phải (Toán)",
        "type": "snippet"
    },
    {
        "label": "\\lessapprox",
        "insertText": "\\lessapprox",
        "detail": "Nhỏ hơn hoặc xấp xỉ (Toán)",
        "type": "snippet"
    },
    {
        "label": "\\gtrsim",
        "insertText": "\\gtrsim",
        "detail": "Lớn hơn hoặc tương đương (Toán)",
        "type": "snippet"
    },
    {
        "label": "\\gtreqless",
        "insertText": "\\gtreqless",
        "detail": "Lớn hơn, bằng hoặc nhỏ hơn (Toán)",
        "type": "snippet"
    },
    {
        "label": "\\lessdot",
        "insertText": "\\lessdot",
        "detail": "Nhỏ hơn có chấm (Toán)",
        "type": "snippet"
    },
    {
        "label": "\\clubsuit",
        "insertText": "\\clubsuit",
        "detail": "Ký hiệu club (Bài Tây)",
        "type": "snippet"
    },
    {
        "label": "\\diamondsuit",
        "insertText": "\\diamondsuit",
        "detail": "Ký hiệu diamond (Bài Tây)",
        "type": "snippet"
    },
    {
        "label": "\\heartsuit",
        "insertText": "\\heartsuit",
        "detail": "Ký hiệu heart (Bài Tây)",
        "type": "snippet"
    },
    {
        "label": "\\spadesuit",
        "insertText": "\\spadesuit",
        "detail": "Ký hiệu spade (Bài Tây)",
        "type": "snippet"
    },
    {
        "label": "\\cmidrule",
        "insertText": "\\cmidrule(${1:trim}){${2:col1}-${3:col2}}",
        "detail": "Đường kẻ giữa rút gọn (bookabs)",
        "type": "snippet"
    },
    {
        "label": "\\arraystretch",
        "insertText": "\\renewcommand{\\arraystretch}{${1:1.5}}",
        "detail": "Hệ số giãn cách dòng trong bảng",
        "type": "snippet"
    },
    {
        "label": "\\angstrom",
        "insertText": "\\angstrom",
        "detail": "Đơn vị Angstrom (siunitx)",
        "type": "snippet"
    },
    {
        "label": "\\barn",
        "insertText": "\\barn",
        "detail": "Đơn vị Barn (siunitx)",
        "type": "snippet"
    },
    {
        "label": "\\bit",
        "insertText": "\\bit",
        "detail": "Đơn vị Bit (siunitx)",
        "type": "snippet"
    },
    {
        "label": "\\byte",
        "insertText": "\\byte",
        "detail": "Đơn vị Byte (siunitx)",
        "type": "snippet"
    },
    {
        "label": "\\lux",
        "insertText": "\\lux",
        "detail": "Đơn vị Lux (siunitx)",
        "type": "snippet"
    },
    {
        "label": "\\bel",
        "insertText": "\\bel",
        "detail": "Đơn vị Bel (siunitx)",
        "type": "snippet"
    },
    {
        "label": "\\decibel",
        "insertText": "\\decibel",
        "detail": "Đơn vị Decibel (siunitx)",
        "type": "snippet"
    },
    {
        "label": "\\deka",
        "insertText": "\\deka",
        "detail": "Tiếp đầu ngữ Deka (siunitx)",
        "type": "snippet"
    },
    {
        "label": "\\Statex",
        "insertText": "\\Statex",
        "detail": "Dòng lệnh không đánh số (Algorithm)",
        "type": "snippet"
    },
    {
        "label": "\\BState",
        "insertText": "\\BState",
        "detail": "Lệnh gán/Trạng thái đặc biệt (Algorithm)",
        "type": "snippet"
    },
    {
        "label": "\\Procedure",
        "insertText": "\\Procedure{${1:name}}{${2:args}}",
        "detail": "Procedure (Algorithm)",
        "type": "snippet"
    },
    {
        "label": "\\EndProcedure",
        "insertText": "\\EndProcedure",
        "detail": "\\EndProcedure (Algorithm)",
        "type": "snippet"
    },
    {
        "label": "\\Function",
        "insertText": "\\Function{${1:name}}{${2:args}}",
        "detail": "Function (Algorithm)",
        "type": "snippet"
    },
    {
        "label": "\\EndFunction",
        "insertText": "\\EndFunction",
        "detail": "\\EndFunction (Algorithm)",
        "type": "snippet"
    }
]

LATEX_PACKAGES = [
    {
        "label": "CJKutf8",
        "insertText": "CJKutf8",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "adjustbox",
        "insertText": "adjustbox",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "algorithm2e",
        "insertText": "algorithm2e",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "amsmath",
        "insertText": "amsmath",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "amsthm",
        "insertText": "amsthm",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "arabtex",
        "insertText": "arabtex",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "array",
        "insertText": "array",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "avm",
        "insertText": "avm",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "babel",
        "insertText": "babel",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "beamerpostr",
        "insertText": "beamerpostr",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "biblatex",
        "insertText": "biblatex",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "bookan",
        "insertText": "bookan",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "bookabs",
        "insertText": "bookabs",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "cancel",
        "insertText": "cancel",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "changes",
        "insertText": "changes",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "charter",
        "insertText": "charter",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "chemfig",
        "insertText": "chemfig",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "circuitikz",
        "insertText": "circuitikz",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "cleveref",
        "insertText": "cleveref",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "courier",
        "insertText": "courier",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "csquotes",
        "insertText": "csquotes",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "dirtytalk",
        "insertText": "dirtytalk",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "draftwatermark",
        "insertText": "draftwatermark",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "enumitem",
        "insertText": "enumitem",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "epigraph",
        "insertText": "epigraph",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "etoolbox",
        "insertText": "etoolbox",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "fancyhdr",
        "insertText": "fancyhdr",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "feynmp-auto",
        "insertText": "feynmp-auto",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "fontenc",
        "insertText": "fontenc",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "fontspec",
        "insertText": "fontspec",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "forest",
        "insertText": "forest",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "gb4e",
        "insertText": "gb4e",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "geometry",
        "insertText": "geometry",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "glossaries",
        "insertText": "glossaries",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "graphicx",
        "insertText": "graphicx",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "helvet",
        "insertText": "helvet",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "hyperref",
        "insertText": "hyperref",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "hyphenat",
        "insertText": "hyphenat",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "imakeidx",
        "insertText": "imakeidx",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "inputenc",
        "insertText": "inputenc",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "lastpage",
        "insertText": "lastpage",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "layout",
        "insertText": "layout",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "lettrine",
        "insertText": "lettrine",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "listings",
        "insertText": "listings",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "lmodern",
        "insertText": "lmodern",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "longtable",
        "insertText": "longtable",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "luatexja",
        "insertText": "luatexja",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "makeidx",
        "insertText": "makeidx",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "marginnote",
        "insertText": "marginnote",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "mathptmx",
        "insertText": "mathptmx",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "mathrsfs",
        "insertText": "mathrsfs",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "mdframed",
        "insertText": "mdframed",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "media9",
        "insertText": "media9",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "mhchem",
        "insertText": "mhchem",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "microtype",
        "insertText": "microtype",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "minted",
        "insertText": "minted",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "modiagram",
        "insertText": "modiagram",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "multicol",
        "insertText": "multicol",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "multirow",
        "insertText": "multirow",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "natbib",
        "insertText": "natbib",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "nomencl",
        "insertText": "nomencl",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "noto",
        "insertText": "noto",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "numprint",
        "insertText": "numprint",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "palatino",
        "insertText": "palatino",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "parskip",
        "insertText": "parskip",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "pdfpages",
        "insertText": "pdfpages",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "pgfgantt",
        "insertText": "pgfgantt",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "pgfplots",
        "insertText": "pgfplots",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "physics",
        "insertText": "physics",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "polyglossia",
        "insertText": "polyglossia",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "ragged2e",
        "insertText": "ragged2e",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "setspace",
        "insertText": "setspace",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "siunitx",
        "insertText": "siunitx",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "soul",
        "insertText": "soul",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "stmaryrd",
        "insertText": "stmaryrd",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "subcaption",
        "insertText": "subcaption",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "subfiles",
        "insertText": "subfiles",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tabularray",
        "insertText": "tabularray",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tabularx",
        "insertText": "tabularx",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tcolorbox",
        "insertText": "tcolorbox",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tgbonum",
        "insertText": "tgbonum",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tgpagella",
        "insertText": "tgpagella",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tgschola",
        "insertText": "tgschola",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tgtermes",
        "insertText": "tgtermes",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tikz",
        "insertText": "tikz",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tikz-3dplot",
        "insertText": "tikz-3dplot",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tikz-cd",
        "insertText": "tikz-cd",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tikz-feynman",
        "insertText": "tikz-feynman",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tikz-qtree",
        "insertText": "tikz-qtree",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "titlesec",
        "insertText": "titlesec",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tocbibind",
        "insertText": "tocbibind",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tocloft",
        "insertText": "tocloft",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "todonotes",
        "insertText": "todonotes",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "ulem",
        "insertText": "ulem",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "url",
        "insertText": "url",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "utopia",
        "insertText": "utopia",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "varioref",
        "insertText": "varioref",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "wrapfig",
        "insertText": "wrapfig",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "xcolor",
        "insertText": "xcolor",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "xeCJK",
        "insertText": "xeCJK",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "xiangqi",
        "insertText": "xiangqi",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "xskak",
        "insertText": "xskak",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "amssymb",
        "insertText": "amssymb",
        "detail": "Ký hiệu toán học AMS",
        "type": "snippet"
    },
    {
        "label": "mathtools",
        "insertText": "mathtools",
        "detail": "Toán học mở rộng (amsmath+)",
        "type": "snippet"
    },
    {
        "label": "caption",
        "insertText": "caption",
        "detail": "Tùy chọn hiển thị tiêu đề hình/bảng",
        "type": "snippet"
    },
    {
        "label": "algorithm",
        "insertText": "algorithm",
        "detail": "Tạo môi trường thuật toán nổi",
        "type": "snippet"
    },
    {
        "label": "algpseudocode",
        "insertText": "algpseudocode",
        "detail": "Ghi thuật toán giả mã",
        "type": "snippet"
    },
    {
        "label": "unicode-math",
        "insertText": "unicode-math",
        "detail": "Font toán học Unicode",
        "type": "snippet"
    }
]

LATEX_ENVIRONMENTS = [
    {
        "label": "Bmatrix",
        "insertText": "Bmatrix",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "Vmatrix",
        "insertText": "Vmatrix",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "abstract",
        "insertText": "abstract",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "algorithm",
        "insertText": "algorithm",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "align",
        "insertText": "align",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "align*",
        "insertText": "align*",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "alignat",
        "insertText": "alignat",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "alignat*",
        "insertText": "alignat*",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "aligned",
        "insertText": "aligned",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "appendix",
        "insertText": "appendix",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "avm",
        "insertText": "avm",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "axis",
        "insertText": "axis",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "bmatrix",
        "insertText": "bmatrix",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "cases",
        "insertText": "cases",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "center",
        "insertText": "center",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "checkboxes",
        "insertText": "checkboxes",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "chemmath",
        "insertText": "chemmath",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "choices",
        "insertText": "choices",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "circuitikz",
        "insertText": "circuitikz",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "code",
        "insertText": "code",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "columns",
        "insertText": "columns",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "description",
        "insertText": "description",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "displaymath",
        "insertText": "displaymath",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "displayquote",
        "insertText": "displayquote",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "document",
        "insertText": "document",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "enumerate",
        "insertText": "enumerate",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "equation",
        "insertText": "equation",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "equation*",
        "insertText": "equation*",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "example",
        "insertText": "example",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "examples",
        "insertText": "examples",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "exe",
        "insertText": "exe",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "feynman",
        "insertText": "feynman",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "figure",
        "insertText": "figure",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "filecontents",
        "insertText": "filecontents",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "flalign",
        "insertText": "flalign",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "flalign*",
        "insertText": "flalign*",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "flushleft",
        "insertText": "flushleft",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "flushright",
        "insertText": "flushright",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "forest",
        "insertText": "forest",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "frame",
        "insertText": "frame",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "gather",
        "insertText": "gather",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "gather*",
        "insertText": "gather*",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "groupplot",
        "insertText": "groupplot",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "itemize",
        "insertText": "itemize",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "list",
        "insertText": "list",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "loglogaxis",
        "insertText": "loglogaxis",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "longtable",
        "insertText": "longtable",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "lstlisting",
        "insertText": "lstlisting",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "math",
        "insertText": "math",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "matrix",
        "insertText": "matrix",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "mdframed",
        "insertText": "mdframed",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "minipage",
        "insertText": "minipage",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "modiagram",
        "insertText": "modiagram",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "multline",
        "insertText": "multline",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "multline*",
        "insertText": "multline*",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "oneparchoices",
        "insertText": "oneparchoices",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "pmatrix",
        "insertText": "pmatrix",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "polaraxis",
        "insertText": "polaraxis",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "proof",
        "insertText": "proof",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "questions",
        "insertText": "questions",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "quotation",
        "insertText": "quotation",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "quote",
        "insertText": "quote",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "scope",
        "insertText": "scope",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "semilogxaxis",
        "insertText": "semilogxaxis",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "semilogyaxis",
        "insertText": "semilogyaxis",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "smallmatrix",
        "insertText": "smallmatrix",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "smithchart",
        "insertText": "smithchart",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "split",
        "insertText": "split",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "subequations",
        "insertText": "subequations",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "table",
        "insertText": "table",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tcolorbox",
        "insertText": "tcolorbox",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "ternaryaxis",
        "insertText": "ternaryaxis",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "thebibliography",
        "insertText": "thebibliography",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "theorem",
        "insertText": "theorem",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tikzcd",
        "insertText": "tikzcd",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tikzfigure",
        "insertText": "tikzfigure",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "tikzpicture",
        "insertText": "tikzpicture",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "trivlist",
        "insertText": "trivlist",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "verbatim",
        "insertText": "verbatim",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "vmatrix",
        "insertText": "vmatrix",
        "detail": "Package/Environment",
        "type": "snippet"
    },
    {
        "label": "dcases",
        "insertText": "dcases",
        "detail": "Hệ phương trình rộng (mathtools)",
        "type": "snippet"
    },
    {
        "label": "minted",
        "insertText": "minted",
        "detail": "Khối mã nguồn màu sắc (Minted)",
        "type": "snippet"
    },
    {
        "label": "algorithmic",
        "insertText": "algorithmic",
        "detail": "Nội dung phương pháp Thuật toán",
        "type": "snippet"
    },
    {
        "label": "tabularx",
        "insertText": "tabularx",
        "detail": "Bảng có độ rộng cột co giãn (X)",
        "type": "snippet"
    },
    {
        "label": "tabulary",
        "insertText": "tabulary",
        "detail": "Bảng có độ rộng cột co giãn tự động lề",
        "type": "snippet"
    },
    {
        "label": "wrapfigure",
        "insertText": "wrapfigure",
        "detail": "Hình ảnh với chữ bao quanh",
        "type": "snippet"
    },
    {
        "label": "subfigure",
        "insertText": "subfigure",
        "detail": "Chia nhỏ hình ảnh phụ",
        "type": "snippet"
    },
    {
        "label": "multicols",
        "insertText": "multicols",
        "detail": "Chia văn bản thành nhiều cột",
        "type": "snippet"
    },
    {
        "label": "block",
        "insertText": "block",
        "detail": "Khung Block (Beamer)",
        "type": "snippet"
    },
    {
        "label": "alertblock",
        "insertText": "alertblock",
        "detail": "Khung cảnh báo (Beamer)",
        "type": "snippet"
    },
    {
        "label": "exampleblock",
        "insertText": "exampleblock",
        "detail": "Khung ví dụ (Beamer)",
        "type": "snippet"
    }
]
