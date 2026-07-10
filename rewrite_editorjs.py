import re

filepath = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/compilation/src/engines/editorjs.py"

with open(filepath, "r") as f:
    content = f.read()

# Define the new robust _render_block method
new_render_block = '''    @staticmethod
    def _render_block(block: dict) -> str:
        import html as _html

        t = block.get("type", "")
        d = block.get("data", {})
        s, san, rb = (
            EditorjsEngine._s,
            EditorjsEngine._san,
            EditorjsEngine._render_block,
        )

        if t == "paragraph":
            align = d.get("alignment", d.get("align", "left"))
            return f'<p style="text-align:{align}">{san(s(d.get("text")))}</p>'

        if t in ("header", "title"):
            lvl = min(max(int(d.get("level", 2)), 1), 6)
            return f'<h{lvl}>{san(s(d.get("text")))}</h{lvl}>'

        if t == "quote":
            cap = san(s(d.get("caption", "")))
            return (
                f'<blockquote>{san(s(d.get("text")))}'
                f'{"<cite>&#8212; " + cap + "</cite>" if cap else ""}</blockquote>'
            )

        if t in ("warning", "alert", "notice", "callout"):
            colors = {
                "warning": "#f0ad4e",
                "alert": "#e74c3c",
                "notice": "#3498db",
                "callout": "#9b59b6",
            }
            c = colors.get(t, "#999")
            title = san(s(d.get("title", d.get("type", ""))))
            msg = san(s(d.get("message", d.get("content", d.get("text", "")))))
            return (
                f'<div style="border-left:4px solid {c};padding:8px 12px;background:#f9f9f9;margin:8px 0">'
                f'{"<strong>" + title + "</strong><br/>" if title else ""}{msg}</div>'
            )

        if t in ("spoiler", "toggle"):
            title = san(s(d.get("title", d.get("text", ""))))
            content = san(s(d.get("content", d.get("message", ""))))
            return f'<details style="border:1px solid #ddd;padding:8px;margin:8px 0"><summary><strong>{title}</strong></summary>{content}</details>'

        if t == "aiText":
            return f'<p style="background:#f0f7ff;padding:6px 10px;border-left:3px solid #3498db">{san(s(d.get("text", d.get("content", ""))))}</p>'

        if t == "delimiter":
            return '<hr style="border:none;border-top:2px solid #ccc;margin:1.5em 0"/>'

        if t in ("breakLine", "divider"):
            return '<hr style="border:none;border-top:1px solid #eee;margin:0.5em 0"/>'

        if t == "raw":
            return san(s(d.get("html", "")))

        if t in ("list", "nestedList"):
            tag = "ol" if d.get("style", "unordered") == "ordered" else "ul"
            return EditorjsEngine._render_list_items(d.get("items", []), tag)

        if t in ("checklist", "nestedChecklist"):
            parts = []
            for item in d.get("items", []):
                chk = "&#x2611;" if item.get("checked") else "&#x2610;"
                txt = san(s(item.get("text", item.get("content", ""))))
                parts.append(f'<p style="margin:2px 0">{chk} {txt}</p>')
            return "".join(parts)

        if t in ("code", "inlineCode"):
            return f'<pre><code>{_html.escape(s(d.get("code", d.get("text", ""))))}</code></pre>'

        if t in ("codeBox", "codeMirror"):
            lang = s(d.get("language", d.get("lang", "")))
            code = _html.escape(s(d.get("code", d.get("content", ""))))
            lbl = (
                f'<div style="font-size:9pt;color:#888;margin-bottom:4px">{lang}</div>'
                if lang
                else ""
            )
            return f'<div>{lbl}<pre style="background:#1e1e1e;color:#d4d4d4;padding:1em;font-family:monospace;font-size:10pt"><code>{code}</code></pre></div>'

        if t == "gist":
            return f'<div style="border:1px solid #ddd;padding:8px">[GitHub Gist: {san(s(d.get("url", d.get("gistId", ""))))}]</div>'

        if t in ("latex", "math"):
            return f'<p style="font-family:monospace;text-align:center">{_html.escape(s(d.get("formula", d.get("math", d.get("text", "")))))}</p>'

        if t == "mermaid":
            return f'<pre style="background:#f4f4f4;padding:1em;font-family:monospace;font-size:9pt">[Mermaid]\\n{_html.escape(s(d.get("code", "")))}</pre>'

        if t in ("image", "simpleImage", "imageCrop", "imageWithLink"):
            url = san(s(d.get("file", {}).get("url", d.get("url", ""))))
            cap = san(s(d.get("caption", "")))
            link = san(s(d.get("link", "")))
            img = f'<img src="{url}" alt="{cap}" style="max-width:100%;display:block;margin:0 auto"/>'
            if link:
                img = f'<a href="{link}">{img}</a>'
            cap_tag = (
                f'<figcaption style="text-align:center;font-size:0.9em;color:#666">{cap}</figcaption>'
                if cap
                else ""
            )
            return f'<figure style="margin:1em 0;text-align:center">{img}{cap_tag}</figure>'

        if t in ("gallery", "groupImage", "carousel"):
            files = d.get("files", d.get("images", []))
            imgs = [
                f'<img src="{san(s(f.get("url", f.get("file", {}).get("url", ""))))}" style="width:30%;margin:4px;vertical-align:top"/>'
                for f in files
                if s(f.get("url", f.get("file", {}).get("url", "")))
            ]
            return f'<div style="margin:1em 0">{"".join(imgs)}</div>' if imgs else ""

        if t in ("audio", "audioPlayer"):
            url = san(s(d.get("file", {}).get("url", d.get("url", ""))))
            title = san(s(d.get("title", "")))
            return f'<div style="border:1px solid #ddd;padding:8px">[Audio: {title or url}]</div>'

        if t == "video":
            url = san(s(d.get("file", {}).get("url", d.get("url", ""))))
            cap = san(s(d.get("caption", "")))
            return f'<div style="border:1px solid #ddd;padding:8px;text-align:center">[Video: {cap or url}]</div>'

        if t in ("embed", "iframe"):
            src = san(
                s(d.get("source", d.get("embed", d.get("url", d.get("src", "")))))
            )
            cap = san(s(d.get("caption", "")))
            return f'<div style="border:1px solid #eee;padding:8px;text-align:center;color:#888">[Embed: {cap or src}]</div>'

        if t in ("attaches", "file"):
            name = san(s(d.get("title", d.get("file", {}).get("name", ""))))
            url = san(s(d.get("file", {}).get("url", "")))
            return f'<div style="border:1px solid #ddd;padding:6px 10px">&#128206; <a href="{url}">{name or url}</a></div>'

        if t == "linkTool":
            link_url = san(s(d.get("link", "")))
            meta = d.get("meta", {})
            title = san(s(meta.get("title", link_url)))
            desc = san(s(meta.get("description", "")))
            return f'<div style="border:1px solid #ddd;padding:8px"><a href="{link_url}"><strong>{title}</strong></a><br/><small>{desc}</small></div>'

        if t in ("linkSearch", "bookmark"):
            url = san(s(d.get("url", d.get("link", ""))))
            title = san(s(d.get("title", d.get("name", url))))
            return f'<p>&#128279; <a href="{url}">{title}</a></p>'

        if t == "table":
            rows = d.get("content", [])
            has_heading = d.get("withHeadings", False)
            if not rows:
                return ""
            html_rows = []
            for i, row in enumerate(rows):
                is_head = i == 0 and has_heading
                cells = "".join(
                    f'<{"th" if is_head else "td"} style="border:1px solid #ccc;padding:5px 8px">{san(s(cell))}</{"th" if is_head else "td"}>'
                    for cell in row
                )
                html_rows.append(f"<tr>{cells}</tr>")
            return f'<table style="border-collapse:collapse;width:100%;margin:1em 0">{"".join(html_rows)}</table>'

        if t == "chart":
            return f'<div style="border:1px solid #ddd;padding:8px;text-align:center;color:#888">[Chart ({san(s(d.get("type","bar")))}): {san(s(d.get("title","")))}]</div>'

        if t == "columns":
            cols = d.get("cols", d.get("blocks", []))
            col_html = []
            for col in cols:
                inner = "".join(rb(b) for b in col.get("blocks", []))
                col_width = 100 // max(len(cols), 1)
                col_html.append(
                    f'<td style="vertical-align:top;padding:4px;width:{col_width}%">{inner}</td>'
                )
            return f'<table style="width:100%;border-collapse:collapse"><tr>{"".join(col_html)}</tr></table>'

        if t == "button":
            link = san(s(d.get("link", "")))
            text = san(s(d.get("text", "")))
            return f'<p><a href="{link}" style="display:inline-block;padding:6px 16px;background:#333;color:#fff;text-decoration:none">{text}</a></p>'

        if t == "kanban":
            parts = []
            for col in d.get("columns", []):
                col_title = san(s(col.get("title", "")))
                cards = "".join(
                    f'<li>{san(s(c.get("text",c) if isinstance(c,dict) else c))}</li>'
                    for c in col.get("cards", [])
                )
                parts.append(
                    f'<div style="display:inline-block;vertical-align:top;width:30%;margin:4px;border:1px solid #ddd;padding:8px"><strong>{col_title}</strong><ul>{cards}</ul></div>'
                )
            return f'<div>{"".join(parts)}</div>'

        if t == "timeline":
            parts = []
            for ev in d.get("events", d.get("items", [])):
                date = san(s(ev.get("date", ev.get("time", ""))))
                text = san(s(ev.get("title", ev.get("text", ""))))
                desc = san(s(ev.get("description", ev.get("content", ""))))
                parts.append(
                    f'<div style="padding:6px 0;border-left:3px solid #333;padding-left:12px;margin:4px 0"><strong>{date}</strong> &#8211; {text}<br/><small>{desc}</small></div>'
                )
            return f'<div>{"".join(parts)}</div>'

        if t == "keyboard":
            return f'<kbd>{san(s(d.get("text", d.get("key", ""))))}</kbd>'

        if t in ("annotation", "tooltip", "footnotes"):
            text = san(s(d.get("text", d.get("content", ""))))
            note = san(s(d.get("note", d.get("tooltip", d.get("footnote", "")))))
            return f'<p>{text} <small style="color:#888">[{note}]</small></p>'

        if t == "comment":
            return f'<p style="color:#888;font-style:italic">&#128172; {san(s(d.get("author","")))} : {san(s(d.get("text",d.get("content",""))))}</p>'

        # UI / Editor state / Formatting variants that don't directly render to HTML blocks
        if t in (
            "undo", "dragDrop", "multiBlockSelection", "premium", "alignment", "indent", "style", "notice", "anchor",
            "styleTune", "textVariant", "textColor", "colorPicker", "marker", "underline", "strikethrough", "changeCase",
            "superscript", "subscript", "textStyle", "hyperlink", "template", "documentProperty", "documentStats",
            "thesaurus", "versionHistory", "compatibilityChecker", "protectDocument", "trackChanges", "macroButton",
            "printPreview", "combineDocuments", "masterDocument", "subdocument", "pageBorder", "pageColor",
            "bordersAndShading", "hyphenation", "quickParts", "diffViewer", "colorPalette", "lineNumbers", "linkPreview",
            "outlineLevel", "textDirection", "textHighlight", "translation"
        ):
            return ""

        # Break lines and layout control
        if t in ("pageBreak", "columnBreak", "evenPageBreak", "oddPageBreak", "sectionBreak", "textWrappingBreak"):
            return '<div style="page-break-after: always;"></div>'

        # Form Controls
        if t in ("formCheckBox", "formComboBox", "formDropdown", "formListBox", "formRadioButton", "formSpinButton", "formToggleButton"):
            lbl = san(s(d.get("label", d.get("text", ""))))
            if "Check" in t or "Radio" in t:
                return f'<div style="margin:4px 0"><input type="{"checkbox" if "Check" in t else "radio"}"/> {lbl}</div>'
            else:
                return f'<div style="margin:4px 0">{lbl}: <span style="display:inline-block;width:100px;border-bottom:1px solid #333;"></span></div>'

        # Document Features - Implemented Correctly
        if t in ("watermark", "watermarkImage"):
            text = san(s(d.get("text", d.get("url", "WATERMARK"))))
            return f'<div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); opacity: 0.15; font-size: 5em; z-index: -1; pointer-events: none; color: #888;">{text}</div>'

        if t == "headerBlock":
            return f'<header style="position: fixed; top: 0; width: 100%; text-align: center; border-bottom: 1px solid #ccc; padding-bottom: 10px; font-size: 0.8em; color: #555;">{san(s(d.get("text", "")))}</header>'
            
        if t == "footerBlock":
            return f'<footer style="position: fixed; bottom: 0; width: 100%; text-align: center; border-top: 1px solid #ccc; padding-top: 10px; font-size: 0.8em; color: #555;">{san(s(d.get("text", "")))}</footer>'

        if t == "pageNumber":
            return '<style>@page { @bottom-right { content: counter(page); font-size: 0.8em; color: #555; } }</style>'

        if t == "coverPage":
            title = san(s(d.get("title", d.get("text", "Trang Bìa"))))
            subtitle = san(s(d.get("subtitle", "")))
            author = san(s(d.get("author", "")))
            return f'<div style="page-break-after: always; height: 80vh; text-align: center; padding-top: 30vh;"><h1 style="font-size: 3em; margin-bottom: 0.2em;">{title}</h1><h3 style="color: #666;">{subtitle}</h3><p style="margin-top: 50px; font-style: italic;">{author}</p></div>'

        if t == "textBox":
            text = san(s(d.get("text", d.get("content", ""))))
            align = san(s(d.get("alignment", "left")))
            return f'<div style="float: {align}; width: 40%; border: 1px solid #333; padding: 15px; margin: 15px; background: #fff; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">{text}</div>'

        if t in ("signature", "digitalSignature"):
            name = san(s(d.get("name", d.get("text", "Ký và ghi rõ họ tên"))))
            title = san(s(d.get("title", "")))
            return f'<div style="text-align: center; width: 250px; float: right; margin-top: 40px; page-break-inside: avoid;"><strong>{title}</strong><br/><br/><br/><br/>_______________________<br/>{name}</div><div style="clear: both;"></div>'

        # Advanced Tables & Lists
        if t in ("tableOfFigures", "tableOfAuthorities", "index", "citation", "crossReference"):
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
            return f'<div style="margin: 20px 0;"><h3>Tài Liệu Tham Khảo</h3>{lis}</div>'

        if t == "footnote":
            txt = san(s(d.get("text", "")))
            num = san(s(d.get("number", "1")))
            return f'<p><sup>[{num}]</sup> {txt}</p>'

        # Shapes and Art
        if t in ("smartArtCycle", "smartArtHierarchy", "smartArtList", "smartArtMatrix", "smartArtProcess", "smartArtPyramid", "smartArtRelationship", "wordArt", "shape", "drawing"):
            title = san(s(d.get("title", d.get("text", t))))
            return f'<div style="border:2px solid #aaa;padding:20px;margin:15px 0;text-align:center;background:#fafafa;border-radius:5px;"><h4 style="margin:0;">{title}</h4><div style="font-size:0.8em;color:#888;">[Sơ đồ/Hình khối]</div></div>'

        # Mail Merge & Addresses
        if t in ("addressBlock", "greetingLine", "envelope", "labelConfig", "letterhead"):
            return f'<div style="border-left: 2px solid #ccc; padding-left: 10px; font-family: monospace; color: #555; margin: 10px 0;">{san(s(d.get("text", d.get("name", ""))))}</div>'

        if t in ("dateAndTime", "datePicker"):
            return f'<div style="text-align: right; font-style: italic; color: #555;">{san(s(d.get("date", d.get("text", ""))))}</div>'

        if t == "mailMerge":
            return f'<span style="background: #eef; padding: 2px 5px; border: 1px dashed #aad;">&lt;&lt; {san(s(d.get("field", "")))} &gt;&gt;</span>'

        # Complex Diagrams
        if t in ("gantt", "kanbanBoard", "mindMap", "verticalTimeline", "directoryTree"):
            title = san(s(d.get("title", t)))
            return f'<div style="border:1px solid #333;padding:20px;margin:15px 0;text-align:center;background:#eef7fa;"><strong>[Biểu đồ: {title}]</strong></div>'

        # Miscellaneous
        if t == "dropCap":
            txt = san(s(d.get("text", "")))
            if txt:
                return f'<p><span style="font-size:2em;float:left;line-height:1;margin-right:4px;">{txt[0]}</span>{txt[1:]}</p>'
            return ""

        if t in ("iframeEmbed", "embed"):
            src = san(s(d.get("src", d.get("url", ""))))
            return f'<iframe src="{src}" style="width: 100%; height: 400px; border: 1px solid #ccc; margin: 15px 0;"></iframe>'

        if t == "jsonViewer":
            return f'<pre style="background: #282a36; color: #f8f8f2; padding: 10px;"><code>{san(s(d.get("json", "")))}</code></pre>'

        if t == "markdownBlock":
            return f'<div style="font-family:monospace;padding:8px;background:#f9f9f9;border:1px solid #ddd;">{san(s(d.get("text", "")))}</div>'

        if t == "caption":
            return f'<figcaption style="text-align:center;font-style:italic;color:#666;">{san(s(d.get("text", "")))}</figcaption>'

        if t == "equationArray":
            import html as _html
            return f'<p style="font-family:monospace;text-align:center">{_html.escape(s(d.get("formula", d.get("math", d.get("text", "")))))}</p>'

        logger.warning("Invalid block content skipped during rendering")
        return ""'''

# Replace the old _render_block
# Find the start of _render_block and the start of _convert_blocks_to_html
start_idx = content.find("    @staticmethod\\n    def _render_block(block: dict) -> str:")
end_idx = content.find("    @staticmethod\\n    def _convert_blocks_to_html")

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_render_block + "\\n\\n" + content[end_idx:]
    with open(filepath, "w") as f:
        f.write(content)
    print("Success")
else:
    print("Failed to find methods")
