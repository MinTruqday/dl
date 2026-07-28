import asyncio
import glob
import html
import json
import os
import re
import tempfile
from urllib.parse import urlparse

import bleach
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings

class EditorjsEngine:

    @staticmethod
    def _s(val) -> str:
        return str(val) if val is not None else ""

    @staticmethod
    def _san(text: str) -> str:
        if not text:
            return ""
        return bleach.clean(
            str(text),
            tags=[
                "a",
                "b",
                "blockquote",
                "br",
                "code",
                "em",
                "i",
                "li",
                "ol",
                "p",
                "pre",
                "s",
                "span",
                "strong",
                "sub",
                "sup",
                "u",
                "ul",
            ],
            attributes={
                "a": ["href", "title"],
                "span": ["class"],
            },
            protocols=["http", "https", "mailto"],
            strip=True,
        )

    @staticmethod
    def _safe_image_url(value: str) -> str:
        url = str(value or "")
        if url.startswith("data:image/"):
            pattern = r"data:image/(?:png|jpeg|jpg|webp);base64,[A-Za-z0-9+/=\s]+"
            if len(url) <= 7 * 1024 * 1024 and re.fullmatch(pattern, url):
                return html.escape(url, quote=True)
            return ""
        parsed = urlparse(url)
        allowed_hosts = {urlparse(settings.MINIO_ENDPOINT).hostname}
        if settings.MINIO_PUBLIC_URL:
            allowed_hosts.add(urlparse(settings.MINIO_PUBLIC_URL).hostname)
        if (
            parsed.scheme in {"http", "https"}
            and parsed.hostname in allowed_hosts
            and not parsed.username
            and not parsed.password
        ):
            return html.escape(url, quote=True)
        return ""

    @staticmethod
    def _safe_link_url(value: str) -> str:
        url = str(value or "").strip()
        if not url or len(url) > 4096:
            return ""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https", "mailto"}:
            return ""
        if parsed.scheme in {"http", "https"} and (
            not parsed.hostname or parsed.username or parsed.password
        ):
            return ""
        return html.escape(url, quote=True)

    @staticmethod
    def _attribute_text(value) -> str:
        text = bleach.clean(str(value or ""), tags=[], strip=True)
        return html.escape(text, quote=True)

    @staticmethod
    def _render_list_items(items, tag: str) -> str:
        s, san = EditorjsEngine._s, EditorjsEngine._san
        parts = []
        for item in items:
            if isinstance(item, dict):
                text = san(s(item.get("content", item.get("text", ""))))
                children = item.get("items", item.get("children", []))
                sub = (
                    EditorjsEngine._render_list_items(children, tag) if children else ""
                )
            else:
                text = san(s(item))
                sub = ""
            parts.append(f"<li>{text}{sub}</li>")
        return f'<{tag}>{"".join(parts)}</{tag}>'

    @staticmethod
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
            if align not in {"left", "right", "center", "justify"}:
                align = "left"
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
            lang = san(s(d.get("language", d.get("lang", ""))))
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
            import html as _html
            code = _html.escape(s(d.get("code", "")))
            return f'<div class="mermaid" style="text-align:center; margin: 15px 0; background:#f4f4f4; padding:10px;">{code}</div>'

        if t in ("image", "simpleImage", "imageCrop", "imageWithLink"):
            url = EditorjsEngine._safe_image_url(
                s(d.get("file", {}).get("url", d.get("url", "")))
            )
            cap = san(s(d.get("caption", "")))
            cap_attribute = EditorjsEngine._attribute_text(d.get("caption", ""))
            link = EditorjsEngine._safe_link_url(d.get("link", ""))
            img = (
                f'<img src="{url}" alt="{cap_attribute}" style="max-width:100%;display:block;margin:0 auto"/>'
                if url
                else ""
            )
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
            imgs = []
            for file_data in files:
                url = EditorjsEngine._safe_image_url(
                    s(file_data.get("url", file_data.get("file", {}).get("url", "")))
                )
                if url:
                    imgs.append(
                        f'<img src="{url}" style="width:30%;margin:4px;vertical-align:top"/>'
                    )
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
            raw_url = s(d.get("file", {}).get("url", ""))
            url = EditorjsEngine._safe_link_url(raw_url)
            label = name or san(raw_url)
            return f'<div style="border:1px solid #ddd;padding:6px 10px"><a href="{url}">{label}</a></div>'

        if t == "linkTool":
            link_url = EditorjsEngine._safe_link_url(d.get("link", ""))
            meta = d.get("meta", {})
            title = san(s(meta.get("title", link_url)))
            desc = san(s(meta.get("description", "")))
            return f'<div style="border:1px solid #ddd;padding:8px"><a href="{link_url}"><strong>{title}</strong></a><br/><small>{desc}</small></div>'

        if t in ("linkSearch", "bookmark"):
            url = EditorjsEngine._safe_link_url(d.get("url", d.get("link", "")))
            title = san(s(d.get("title", d.get("name", url))))
            return f'<p><a href="{url}">{title}</a></p>'

        if t == "drawing":
            return '<div style="border:1px solid #eee;padding:8px;text-align:center;color:#aaa">[Drawing]</div>'

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
            link = EditorjsEngine._safe_link_url(d.get("link", ""))
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
            return f'<p style="color:#888;font-style:italic">Binh luan tu {san(s(d.get("author","")))} : {san(s(d.get("text",d.get("content",""))))}</p>'

        if t in (
            "undo", "dragDrop", "multiBlockSelection", "premium", "alignment", "indent", "style", "notice", "anchor",
            "styleTune", "textVariant", "textColor", "colorPicker", "marker", "underline", "strikethrough", "changeCase",
            "superscript", "subscript", "textStyle", "hyperlink", "template", "documentProperty", "documentStats",
            "thesaurus", "versionHistory", "compatibilityChecker", "protectDocument", "trackChanges", "macroButton",
            "printPreview", "combineDocuments", "masterDocument", "subdocument", "pageBorder", "pageColor",
            "bordersAndShading", "hyphenation", "quickParts", "diffViewer", "colorPalette", "lineNumbers", "linkPreview",
            "outlineLevel", "textDirection", "textHighlight", "translation",
            "readAloud", "focusMode", "gridlines", "accessibilityChecker", "restrictEditing", "textEffects",
            "focusLine", "typewriterMode", "editorScore", "smartPaste", "revealFormatting", "widowOrphanControl",
            "autoCorrect", "shrinkToFit", "clearFormatting", "goTo", "tabStops",
            "doubleStrikethrough", "smallCaps", "hiddenText", "characterSpacing", "textScaling",
            "splitWindow", "synchronousScrolling",
            "outlineView", "draftView", "webLayout", "ruler",
            "hyphenationZone", "gutterMargin", "firstLineIndent", "printLayout", "readMode",
            "navigationPane", "balloons", "documentInspector",
            "immersiveReader", "researcher", "selectionPane", "wrapText", "bringForward",
            "removeBackground", "artisticEffects", "pasteSpecial", "keepWithNext", "ligatures",
            "reflection", "glow", "softEdges", "textOutline", "textFill",
            "groupShapes", "alignObjects", "compressPictures", "lineFocus",
            "pageMovement", "resumeAssistant", "autoFormatAsYouType",
            "mailMergeRecipients", "citationStyle", "kerningForFonts",
            "orientation", "paperSize", "verticalAlignment", "blankPage", "pageBreakBefore",
            "keepLinesTogether", "suppressLineNumbers", "dontHyphenate", "zoom", "onePage",
            "multiplePages", "pageWidth", "newWindow", "viewSideBySide", "switchWindows",
            "drawTable", "eraser", "mergeCells", "splitCells", "splitTable",
            "autoFit", "distributeRows", "distributeColumns", "cellMargins", "sortTable",
            "repeatHeaderRows", "tableFormula", "viewGridlinesTable", "insertAbove", "insertBelow",
            "3DRotation", "bevel", "pictureCorrections", "pictureColor", "changePicture",
            "resetPicture", "pictureBorder", "pictureLayout", "cropToShape", "cropAspectRatio",
            "screenshot", "symbol", "textFromFile", "dropCapLinesToDrop", "showFormattingMarks",
            "richTextContentControl", "plainTextContentControl", "pictureContentControl", "buildingBlockGallery", "comboBoxContentControl",
            "dropDownListControl", "datePickerControl", "checkBoxControl", "designMode", "controlProperties",
            "groupControls", "documentTemplate", "cOMAddIns", "wordAddIns", "xMLMappingPane",
            "editRecipientList", "highlightMergeFields", "mailMergeRules", "matchFields", "updateLabels",
            "previewResults", "findRecipient", "autoCheckForErrors", "finishAndMerge", "markCitation",
            "markEntry", "updateTable", "addTextToTOC", "altText", "smartLookup"
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
            align = s(d.get("alignment", "left"))
            if align not in {"left", "right"}:
                align = "left"
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
            return f'<div style="border:2px solid #2b6cb0;padding:30px;margin:20px 0;text-align:center;background:linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);border-radius:8px;box-shadow: 2px 2px 5px rgba(0,0,0,0.1);"><h3 style="margin:0;color:#2b6cb0;">{title}</h3></div>'

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
            return f'<div style="border:1px solid #ccc;padding:8px">[Embed: {src}]</div>'

        if t == "jsonViewer":
            return f'<pre style="background: #282a36; color: #f8f8f2; padding: 10px;"><code>{san(s(d.get("json", "")))}</code></pre>'

        if t == "markdownBlock":
            return f'<div style="font-family:monospace;padding:8px;background:#f9f9f9;border:1px solid #ddd;">{san(s(d.get("text", "")))}</div>'

        if t == "caption":
            return f'<figcaption style="text-align:center;font-style:italic;color:#666;">{san(s(d.get("text", "")))}</figcaption>'

        if t == "equationArray":
            import html as _html
            return f'<p style="font-family:monospace;text-align:center">{_html.escape(s(d.get("formula", d.get("math", d.get("text", "")))))}</p>'

        if t == "field":
            return f'<span style="background: #f0f0f0; padding: 2px 4px; border: 1px dashed #ccc; font-family: monospace;">{{{san(s(d.get("code", d.get("content", d.get("name", "")))) )}}}</span>'

        if t == "sparklines":
            values = []
            for raw in re.split(r"[\s,;]+", s(d.get("values", "")).strip())[:100]:
                if not raw:
                    continue
                try:
                    value = float(raw)
                except ValueError:
                    continue
                if value == value and abs(value) != float("inf"):
                    values.append(value)
            if len(values) < 2:
                return ""
            low = min(values)
            high = max(values)
            span = high - low or 1
            width = 240
            height = 60
            points = " ".join(
                f"{index * width / (len(values) - 1):.2f},{height - ((value - low) / span * height):.2f}"
                for index, value in enumerate(values)
            )
            return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Sparkline"><polyline fill="none" stroke="#2563eb" stroke-width="3" points="{points}"/></svg>'

        if t == "oleObject":
            name = san(s(d.get("objectId", d.get("name", d.get("title", "Embedded Object")))))
            return f'<div style="border: 2px solid #555; padding: 15px; background: #f9f9f9; width: 250px; text-align: center; margin: 20px auto; border-radius: 8px;"><strong>{name}</strong><br/><small style="color:#666;">Double-click to open</small></div>'

        if t in ("convertTextToTable", "convertTableToText", "tableAutoFormat"):
            content = san(s(d.get("content", "")))
            return f'<div style="margin: 10px 0; padding: 10px; border: 1px solid #cbd5e1; background: #f8fafc;">{content}</div>'

        if t == "digitalSignatureLine":
            name = san(s(d.get("content", d.get("name", "Ky va ghi ro ho ten"))))
            return f'<div style="width: 300px; margin: 40px auto; text-align: center;"><div style="font-size: 2em; float: left; margin-top: -15px; font-family: monospace;">X</div><hr style="border-top: 2px solid #000; margin-bottom: 5px; clear: both;" /><strong>{name}</strong></div>'

        if t == "phoneticGuide":
            ruby = san(s(d.get("ruby", d.get("content", ""))))
            base = san(s(d.get("base", "")))
            if ruby and base:
                return f'<ruby>{base}<rt>{ruby}</rt></ruby>'
            return f'<span>{ruby or base}</span>'

        logger.warning("Invalid block content skipped during rendering")
        return ""

    @staticmethod
    def _convert_blocks_to_html(blocks: list) -> str:
        CSS = (
            "@page { margin: 2.5cm 2cm; }"
            "body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 12pt; line-height: 1.7; color: #222; }"
            "h1 { font-size: 2em; } h2 { font-size: 1.6em; } h3 { font-size: 1.3em; } h4,h5,h6 { font-size: 1.1em; }"
            "h1,h2,h3,h4,h5,h6 { font-weight: bold; margin: 0.8em 0 0.3em; }"
            "p { margin: 0.5em 0; }"
            "blockquote { border-left: 4px solid #ccc; margin: 1em 2em; padding: 0.5em 1em; color: #555; font-style: italic; }"
            "pre { background: #f4f4f4; padding: 1em; font-family: monospace; font-size: 10pt; }"
            "table { border-collapse: collapse; width: 100%; margin: 1em 0; }"
            "th, td { border: 1px solid #ccc; padding: 5px 8px; }"
            "th { background: #f0f0f0; font-weight: bold; }"
            "hr { border: none; border-top: 2px solid #ccc; margin: 1.5em 0; }"
            "figure { text-align: center; margin: 1em 0; }"
            "figcaption { font-size: 0.9em; color: #666; }"
            "img { max-width: 100%; }"
            "a { color: #2c5282; }"
            "details { border: 1px solid #ddd; padding: 8px; margin: 8px 0; }"
            "kbd { background: #f4f4f4; border: 1px solid #ccc; border-radius: 3px; padding: 1px 5px; font-family: monospace; }"
            ".DocLibDoubleStrikethrough { text-decoration-line: line-through; text-decoration-style: double; }"
            ".DocLibHiddenText { opacity: 0.35; text-decoration: underline dashed; }"
            ".DocLibSmallCaps { font-variant: small-caps; }"
            ".doclib-text-effects { text-shadow: 1px 1px 2px rgba(15, 23, 42, 0.35); }"
        )
        parts = [
            f'<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"/><style>{CSS}</style></head><body>'
        ]
        for block in blocks:
            rendered = EditorjsEngine._render_block(block)
            if rendered:
                parts.append(rendered)
        parts.append("</body></html>")
        return "\n".join(parts)

    @staticmethod
    def _parse_content(content: str) -> list:
        if len(content.encode("utf-8")) > settings.MAX_COMPILE_INPUT_BYTES:
            raise ValueError("Kích thước nội dung biên dịch không hợp lệ")
        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError("Định dạng dữ liệu nội dung tài liệu không hợp lệ")
        blocks = parsed_content.get("blocks", []) if isinstance(parsed_content, dict) else []
        if not isinstance(blocks, list) or not blocks or len(blocks) > 5000:
            raise ValueError("Tài liệu không chứa danh sách khối hợp lệ")
        return blocks

    @staticmethod
    async def compile_to_pdf(content: str) -> bytes:
        from src.engines.latex import compile_semaphore, run_process

        blocks = EditorjsEngine._parse_content(content)
        html_content = EditorjsEngine._convert_blocks_to_html(blocks)
        async with compile_semaphore:
            with tempfile.TemporaryDirectory(prefix="doclib_editorjs_") as temp_dir:
                html_path = os.path.join(temp_dir, "document.html")
                pdf_path = os.path.join(temp_dir, "document.pdf")
                with open(html_path, "w", encoding="utf-8") as stream:
                    stream.write(html_content)
                await run_process(
                    [
                        "weasyprint",
                        html_path,
                        pdf_path,
                    ],
                    temp_dir,
                )
                if not os.path.isfile(pdf_path):
                    raise ValueError("Quá trình xuất không tạo được tệp PDF")
                size = os.path.getsize(pdf_path)
                if size < 1 or size > settings.MAX_COMPILE_OUTPUT_BYTES:
                    raise ValueError("Kích thước tệp kết quả không hợp lệ")
                with open(pdf_path, "rb") as stream:
                    return stream.read()

    @staticmethod
    async def export_to_format(content: str, target_format: str) -> bytes:
        from src.engines.latex import compile_semaphore, run_process

        if target_format not in {"docx", "html"}:
            raise ValueError("Định dạng xuất không được hỗ trợ")
        blocks = EditorjsEngine._parse_content(content)
        html_content = EditorjsEngine._convert_blocks_to_html(blocks)
        async with compile_semaphore:
            with tempfile.TemporaryDirectory(prefix="doclib_editorjs_export_") as temp_dir:
                html_path = os.path.join(temp_dir, "document.html")
                output_path = os.path.join(temp_dir, f"document.{target_format}")
                with open(html_path, "w", encoding="utf-8") as stream:
                    stream.write(html_content)
                await run_process(
                    ["pandoc", html_path, "-o", output_path],
                    temp_dir,
                )
                if not os.path.isfile(output_path):
                    raise ValueError("Quá trình xuất không tạo được tệp kết quả")
                size = os.path.getsize(output_path)
                if size < 1 or size > settings.MAX_COMPILE_OUTPUT_BYTES:
                    raise ValueError("Kích thước tệp kết quả không hợp lệ")
                with open(output_path, "rb") as stream:
                    return stream.read()
