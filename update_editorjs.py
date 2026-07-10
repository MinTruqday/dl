import os

filepath = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/compilation/src/engines/editorjs.py"

with open(filepath, "r") as f:
    content = f.read()

# 1. watermark
content = content.replace(
    '        if t in ("watermark", "watermarkImage"):\n            return ""',
    '''        if t in ("watermark", "watermarkImage"):
            text = san(s(d.get("text", d.get("url", "WATERMARK"))))
            return f'<div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); opacity: 0.15; font-size: 5em; z-index: -1; pointer-events: none; color: #888;">{text}</div>' '''
)

# 2. pageNumber, headerBlock, footerBlock
content = content.replace(
    '        if t in ("headerBlock", "footerBlock", "pageNumber", "bordersAndShading", "hyphenation", "quickParts"):\n            return ""',
    '''        if t in ("bordersAndShading", "hyphenation", "quickParts"):
            return ""

        if t == "headerBlock":
            return f'<header style="position: fixed; top: 0; width: 100%; text-align: center; border-bottom: 1px solid #ccc; padding-bottom: 10px; font-size: 0.8em; color: #555;">{san(s(d.get("text", "")))}</header>'
            
        if t == "footerBlock":
            return f'<footer style="position: fixed; bottom: 0; width: 100%; text-align: center; border-top: 1px solid #ccc; padding-top: 10px; font-size: 0.8em; color: #555;">{san(s(d.get("text", "")))}</footer>'

        if t == "pageNumber":
            # For PDF/Weasyprint, use CSS counters
            return '<style>@page { @bottom-right { content: counter(page); font-size: 0.8em; color: #555; } }</style>' '''
)

# 3. coverPage
content = content.replace(
    '''        if t in ("datePicker", "coverPage", "mailMerge"):
            title = san(s(d.get("title", d.get("text", t))))
            return f'<div style="font-style:italic;color:#555">[{t}: {title}]</div>' ''',
    '''        if t in ("datePicker", "mailMerge"):
            title = san(s(d.get("title", d.get("text", t))))
            return f'<div style="font-style:italic;color:#555">[{t}: {title}]</div>'

        if t == "coverPage":
            title = san(s(d.get("title", d.get("text", "Trang Bìa"))))
            subtitle = san(s(d.get("subtitle", "")))
            author = san(s(d.get("author", "")))
            return f'<div style="page-break-after: always; height: 80vh; text-align: center; padding-top: 30vh;"><h1 style="font-size: 3em; margin-bottom: 0.2em;">{title}</h1><h3 style="color: #666;">{subtitle}</h3><p style="margin-top: 50px; font-style: italic;">{author}</p></div>' '''
)

# 4. textBox
content = content.replace(
    '''        if t in ("smartArtCycle", "smartArtHierarchy", "smartArtList", "smartArtMatrix", "smartArtProcess", "smartArtPyramid", "smartArtRelationship", "wordArt", "shape", "textBox", "drawing"):
            title = san(s(d.get("title", d.get("text", t))))
            return f'<div style="border:2px solid #aaa;padding:12px;margin:8px 0;text-align:center;background:#fafafa"><strong>[{t}]</strong><br/>{title}</div>' ''',
    '''        if t in ("smartArtCycle", "smartArtHierarchy", "smartArtList", "smartArtMatrix", "smartArtProcess", "smartArtPyramid", "smartArtRelationship", "wordArt", "shape", "drawing"):
            title = san(s(d.get("title", d.get("text", t))))
            return f'<div style="border:2px solid #aaa;padding:12px;margin:8px 0;text-align:center;background:#fafafa"><strong>[{t}]</strong><br/>{title}</div>'

        if t == "textBox":
            text = san(s(d.get("text", d.get("content", ""))))
            align = san(s(d.get("alignment", "left")))
            return f'<div style="float: {align}; width: 40%; border: 1px solid #333; padding: 15px; margin: 15px; background: #fff; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">{text}</div>' '''
)

# 5. signature
content = content.replace(
    '''        if t in ("addressBlock", "greetingLine", "dateAndTime", "envelope", "labelConfig", "letterhead", "digitalSignature", "signature"):
            return f'<div style="font-family:monospace;color:#555">[{t}: {san(s(d.get("text", d.get("name", ""))))}]</div>' ''',
    '''        if t in ("addressBlock", "greetingLine", "dateAndTime", "envelope", "labelConfig", "letterhead", "digitalSignature"):
            return f'<div style="font-family:monospace;color:#555">[{t}: {san(s(d.get("text", d.get("name", ""))))}]</div>'

        if t == "signature":
            name = san(s(d.get("name", d.get("text", "Ký và ghi rõ họ tên"))))
            title = san(s(d.get("title", "")))
            return f'<div style="text-align: center; width: 250px; float: right; margin-top: 40px; page-break-inside: avoid;"><strong>{title}</strong><br/><br/><br/><br/>_______________________<br/>{name}</div><div style="clear: both;"></div>' '''
)

# 6. tableOfContents & bibliography
content = content.replace(
    '''        if t in ("tableOfContents", "tableOfFigures", "tableOfAuthorities", "index", "bibliography", "citation", "crossReference"):
            items = d.get("items", d.get("list", []))
            if not items:
                return f'<div style="border:1px dashed #ccc;padding:8px">[{t}]</div>'
            lis = "".join(f'<li>{san(s(i.get("text", i)))}</li>' for i in items)
            return f'<ul>{lis}</ul>' ''',
    '''        if t in ("tableOfFigures", "tableOfAuthorities", "index", "citation", "crossReference"):
            items = d.get("items", d.get("list", []))
            if not items:
                return f'<div style="border:1px dashed #ccc;padding:8px">[{t}]</div>'
            lis = "".join(f'<li>{san(s(i.get("text", i)))}</li>' for i in items)
            return f'<ul>{lis}</ul>'

        if t == "tableOfContents":
            items = d.get("items", d.get("list", []))
            if not items:
                return ""
            lis = "".join(
                f'<div style="display: flex; margin-bottom: 5px;"><span style="flex-shrink: 0;">{san(s(i.get("text", i)))}</span><span style="flex-grow: 1; border-bottom: 1px dotted #000; margin: 0 10px; position: relative; top: -5px;"></span><span style="flex-shrink: 0;">{san(s(i.get("page", "")))}</span></div>'
                for i in items
            )
            return f'<div style="margin: 20px 0;"><h3>Mục Lục</h3>{lis}</div>'

        if t == "bibliography":
            items = d.get("items", d.get("list", []))
            if not items:
                return ""
            lis = "".join(f'<p style="padding-left: 2em; text-indent: -2em; margin-bottom: 10px;">{san(s(i.get("text", i)))}</p>' for i in items)
            return f'<div style="margin: 20px 0;"><h3>Tài Liệu Tham Khảo</h3>{lis}</div>' '''
)

with open(filepath, "w") as f:
    f.write(content)
