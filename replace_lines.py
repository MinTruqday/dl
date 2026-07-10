filepath = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/compilation/src/engines/editorjs.py"

with open(filepath, "r") as f:
    lines = f.readlines()

new_block = """
        if t == "comment":
            return f'<p style="color:#888;font-style:italic">Binh luan tu {san(s(d.get("author","")))} : {san(s(d.get("text",d.get("content",""))))}</p>'

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

        if t in ("pageBreak", "columnBreak", "evenPageBreak", "oddPageBreak", "sectionBreak", "textWrappingBreak"):
            return '<div style="page-break-after: always;"></div>'

        if t in ("formCheckBox", "formComboBox", "formDropdown", "formListBox", "formRadioButton", "formSpinButton", "formToggleButton"):
            lbl = san(s(d.get("label", d.get("text", ""))))
            if "Check" in t or "Radio" in t:
                return f'<div style="margin:4px 0"><input type="{"checkbox" if "Check" in t else "radio"}"/> {lbl}</div>'
            else:
                return f'<div style="margin:4px 0">{lbl}: <span style="display:inline-block;width:100px;border-bottom:1px solid #333;"></span></div>'

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
            title = san(s(d.get("title", d.get("text", "Trang Bia"))))
            subtitle = san(s(d.get("subtitle", "")))
            author = san(s(d.get("author", "")))
            return f'<div style="page-break-after: always; height: 80vh; text-align: center; padding-top: 30vh;"><h1 style="font-size: 3em; margin-bottom: 0.2em;">{title}</h1><h3 style="color: #666;">{subtitle}</h3><p style="margin-top: 50px; font-style: italic;">{author}</p></div>'

        if t == "textBox":
            text = san(s(d.get("text", d.get("content", ""))))
            align = san(s(d.get("alignment", "left")))
            return f'<div style="float: {align}; width: 40%; border: 1px solid #333; padding: 15px; margin: 15px; background: #fff; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">{text}</div>'

        if t in ("signature", "digitalSignature"):
            name = san(s(d.get("name", d.get("text", "Ky va ghi ro ho ten"))))
            title = san(s(d.get("title", "")))
            return f'<div style="text-align: center; width: 250px; float: right; margin-top: 40px; page-break-inside: avoid;"><strong>{title}</strong><br/><br/><br/><br/>_______________________<br/>{name}</div><div style="clear: both;"></div>'

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
            return f'<div style="margin: 20px 0;"><h3>Muc Luc</h3>{lis}</div>'

        if t == "bibliography":
            items = d.get("items", d.get("list", []))
            if not items:
                return ""
            lis = "".join(f'<p style="padding-left: 2em; text-indent: -2em; margin-bottom: 10px;">{san(s(i.get("text", i)))}</p>' for i in items)
            return f'<div style="margin: 20px 0;"><h3>Tai Lieu Tham Khao</h3>{lis}</div>'

        if t == "footnote":
            txt = san(s(d.get("text", "")))
            num = san(s(d.get("number", "1")))
            return f'<p><sup>[{num}]</sup> {txt}</p>'

        if t in ("smartArtCycle", "smartArtHierarchy", "smartArtList", "smartArtMatrix", "smartArtProcess", "smartArtPyramid", "smartArtRelationship", "wordArt", "shape", "drawing"):
            title = san(s(d.get("title", d.get("text", t))))
            return f'<div style="border:2px solid #aaa;padding:20px;margin:15px 0;text-align:center;background:#fafafa;border-radius:5px;"><h4 style="margin:0;">{title}</h4><div style="font-size:0.8em;color:#888;">Hinh khoi so do</div></div>'

        if t in ("addressBlock", "greetingLine", "envelope", "labelConfig", "letterhead"):
            return f'<div style="border-left: 2px solid #ccc; padding-left: 10px; font-family: monospace; color: #555; margin: 10px 0;">{san(s(d.get("text", d.get("name", ""))))}</div>'

        if t in ("dateAndTime", "datePicker"):
            return f'<div style="text-align: right; font-style: italic; color: #555;">{san(s(d.get("date", d.get("text", ""))))}</div>'

        if t == "mailMerge":
            return f'<span style="background: #eef; padding: 2px 5px; border: 1px dashed #aad;">&lt;&lt; {san(s(d.get("field", "")))} &gt;&gt;</span>'

        if t in ("gantt", "kanbanBoard", "mindMap", "verticalTimeline", "directoryTree"):
            title = san(s(d.get("title", t)))
            return f'<div style="border:1px solid #333;padding:20px;margin:15px 0;text-align:center;background:#eef7fa;"><strong>Bieu do: {title}</strong></div>'

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

"""

# line 271 corresponds to `if t == "comment":`
# line 382 corresponds to `logger.warning("Invalid block content skipped during rendering")`

out_lines = lines[:271] + [new_block.lstrip("\n") + "\n"] + lines[380:]

with open(filepath, "w") as f:
    f.writelines(out_lines)
