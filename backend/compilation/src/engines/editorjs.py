import asyncio
import glob
import json
import os
import re
import tempfile

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
        text = re.sub(
            r"<(script|iframe|object|applet)(.*?)>(.*?)</\1>",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        text = re.sub(r' on\w+\s*=\s*["\'][^"\']*["\']', "", text, flags=re.IGNORECASE)
        return text

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
            return f'<pre style="background:#f4f4f4;padding:1em;font-family:monospace;font-size:9pt">[Mermaid]\n{_html.escape(s(d.get("code", "")))}</pre>'

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

        if t in ("embed", "gif", "telegramPost", "iframe"):
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
            link = san(s(d.get("link", "")))
            text = san(s(d.get("text", "")))
            return f'<p><a href="{link}" style="display:inline-block;padding:6px 16px;background:#333;color:#fff;text-decoration:none">{text}</a></p>'

        if t == "quiz":
            q = san(s(d.get("question", "")))
            opts = "".join(
                f'<li>{san(s(o.get("text",o) if isinstance(o,dict) else o))}</li>'
                for o in d.get("options", [])
            )
            return f'<div style="border:1px solid #ddd;padding:8px"><strong>Quiz:</strong> {q}<ol>{opts}</ol></div>'

        if t == "poll":
            q = san(s(d.get("question", d.get("title", ""))))
            opts = "".join(
                f'<li>{san(s(o.get("text",o) if isinstance(o,dict) else o))}</li>'
                for o in d.get("options", [])
            )
            return f'<div style="border:1px solid #ddd;padding:8px"><strong>Poll:</strong> {q}<ul>{opts}</ul></div>'

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

        if t == "steps":
            parts = [
                f'<div style="margin:4px 0"><strong>Step {i}:</strong> {san(s(item.get("text", item.get("title", "")) if isinstance(item, dict) else item))}</div>'
                for i, item in enumerate(d.get("items", d.get("steps", [])), 1)
            ]
            return f'<div>{"".join(parts)}</div>'

        if t == "pricing":
            parts = [
                f'<div style="display:inline-block;border:1px solid #ddd;padding:8px 12px;margin:4px;vertical-align:top"><strong>{san(s(p.get("title",p.get("name",""))))}</strong><br/>{san(s(p.get("price","")))}</div>'
                for p in d.get("plans", d.get("items", []))
            ]
            return f'<div>{"".join(parts)}</div>'

        if t == "testimonial":
            return f'<blockquote style="border-left:4px solid #ddd;padding:8px 12px;font-style:italic">{san(s(d.get("text",d.get("content",""))))}<cite> &#8212; {san(s(d.get("author",d.get("name",""))))}</cite></blockquote>'

        if t == "personality":
            photo = san(s(d.get("photo", "")))
            img = (
                f'<img src="{photo}" style="width:48px;height:48px;border-radius:50%;margin-right:8px;vertical-align:middle"/>'
                if photo
                else ""
            )
            return f'<div style="border:1px solid #eee;padding:8px">{img}<strong>{san(s(d.get("name","")))}</strong><br/><small>{san(s(d.get("description","")))}</small></div>'

        if t in ("countdown", "progressBar", "progress"):
            label = san(s(d.get("label", d.get("title", ""))))
            value = d.get("progress", d.get("percent", d.get("value", 0)))
            return f'<div>{label}<div style="background:#eee;height:12px;border-radius:6px;overflow:hidden"><div style="background:#333;height:100%;width:{value}%"></div></div><small>{value}%</small></div>'

        if t == "flipbox":
            front_raw = d.get("front", "")
            back_raw = d.get("back", "")
            front = san(
                s(
                    front_raw.get("text", "")
                    if isinstance(front_raw, dict)
                    else front_raw
                )
            )
            back = san(
                s(back_raw.get("text", "") if isinstance(back_raw, dict) else back_raw)
            )
            return f'<div style="border:1px solid #ddd;padding:8px"><strong>Front:</strong> {front}<br/><strong>Back:</strong> {back}</div>'

        if t == "badge":
            return f'<span style="display:inline-block;background:{d.get("color","#333")};color:#fff;padding:2px 8px;border-radius:12px;font-size:0.8em">{san(s(d.get("text","")))}</span>'

        if t == "keyboard":
            return f'<kbd>{san(s(d.get("text", d.get("key", ""))))}</kbd>'

        if t in ("annotation", "tooltip", "footnotes"):
            text = san(s(d.get("text", d.get("content", ""))))
            note = san(s(d.get("note", d.get("tooltip", d.get("footnote", "")))))
            return f'<p>{text} <small style="color:#888">[{note}]</small></p>'

        if t == "comment":
            return f'<p style="color:#888;font-style:italic">&#128172; {san(s(d.get("author","")))} : {san(s(d.get("text",d.get("content",""))))}</p>'

        if t in (
            "undo",
            "dragDrop",
            "multiBlockSelection",
            "premium",
            "alignment",
            "indent",
            "style",
            "notice",
            "anchor",
            "styleTune",
            "textVariant",
            "textColor",
            "colorPicker",
            "marker",
            "underline",
            "strikethrough",
            "changeCase",
            "superscript",
            "subscript",
            "textStyle",
            "hyperlink",
            "linkSearch",
            "template",
        ):
            return ""

        logger.warning("Đã bỏ qua nội dung không hợp lệ")
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
    async def compile_to_pdf(content: str) -> bytes:
        try:
            parsed_content = json.loads(content)
            blocks = (
                parsed_content.get("blocks", [])
                if isinstance(parsed_content, dict)
                else []
            )
        except json.JSONDecodeError as e:
            raise Exception(f"Định dạng nội dung tài liệu không hợp lệ: {e}")

        if not blocks:
            raise Exception("Tài liệu không có nội dung hợp lệ")

        html_content = EditorjsEngine._convert_blocks_to_html(blocks)

        job_id = str(uuid7())
        temp_dir = tempfile.gettempdir()
        html_path = os.path.join(temp_dir, f"{job_id}.html")
        pdf_path = os.path.join(temp_dir, f"{job_id}.pdf")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                "timeout",
                "-k",
                "35",
                "30",
                "pandoc",
                html_path,
                "-o",
                pdf_path,
                "--pdf-engine=weasyprint",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024 * 2,
            )
            await asyncio.wait_for(
                process.communicate(), timeout=settings.LONG_PROCESS_TIMEOUT
            )

            if not os.path.exists(pdf_path):
                logger.error("Lỗi xuất tài liệu PDF")
                raise Exception("Lỗi xuất tài liệu")

            with open(pdf_path, "rb") as f:
                return f.read()

        except asyncio.TimeoutError as e:
            if process:
                try:
                    process.kill()
                except Exception as e:
                    logger.exception("Lỗi dừng tác vụ biên dịch")
            raise Exception("Hết thời gian chờ quá trình biên dịch tài liệu")

        finally:
            for filepath in glob.glob(os.path.join(temp_dir, f"{job_id}.*")):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.exception("Lỗi dọn dẹp tệp tạm thời")

    @staticmethod
    async def export_to_format(content: str, target_format: str) -> bytes:
        try:
            parsed_content = json.loads(content)
            blocks = (
                parsed_content.get("blocks", [])
                if isinstance(parsed_content, dict)
                else []
            )
        except json.JSONDecodeError as e:
            raise Exception(f"Định dạng nội dung tài liệu không hợp lệ: {e}")

        if not blocks:
            raise Exception("Tài liệu không có nội dung hợp lệ")

        html_content = EditorjsEngine._convert_blocks_to_html(blocks)

        job_id = str(uuid7())
        temp_dir = tempfile.gettempdir()
        html_path = os.path.join(temp_dir, f"{job_id}.html")
        out_path = os.path.join(temp_dir, f"{job_id}.{target_format}")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                "timeout",
                "-k",
                "35",
                "30",
                "pandoc",
                html_path,
                "-o",
                out_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024 * 2,
            )
            await asyncio.wait_for(
                process.communicate(), timeout=settings.LONG_PROCESS_TIMEOUT
            )

            if not os.path.exists(out_path):
                logger.error("Lỗi xuất tài liệu")
                raise Exception("Lỗi xuất tài liệu")

            with open(out_path, "rb") as f:
                return f.read()

        except asyncio.TimeoutError as e:
            if process:
                try:
                    process.kill()
                except Exception as e:
                    logger.exception("Lỗi dừng tác vụ biên dịch")
            raise Exception("Hết thời gian chờ quá trình xuất tài liệu")

        finally:
            for filepath in glob.glob(os.path.join(temp_dir, f"{job_id}.*")):
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.exception("Lỗi dọn dẹp tệp tạm thời")
