import os
import re

components = {
    "DocLibDoubleStrikethrough": {
        "inline": True,
        "title": "DocLib Double Strikethrough",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M5 10H19M5 14H19M8 4L16 20\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibSmallCaps": {
        "inline": True,
        "title": "DocLib Small Caps",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M5 18V6H13V8H7V11H12V13H7V18H5ZM16 18V10H22V12H18V14H21V16H18V18H16Z\" fill=\"currentColor\"/></svg>"
    },
    "DocLibHiddenText": {
        "inline": True,
        "title": "DocLib Hidden Text",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M3 3L21 21M10.5 10.677C10.189 11.03 10 11.493 10 12C10 13.1046 10.8954 14 12 14C12.507 14 12.97 13.811 13.323 13.5M17.657 16.657C16.101 17.765 14.154 18.5 12 18.5C6.47715 18.5 2 12 2 12C2 12 3.636 8.5 6.343 6.343M6.343 6.343C7.899 5.235 9.846 4.5 12 4.5C17.5228 4.5 22 11 22 11C22 11 20.364 14.5 17.657 16.657M6.343 6.343L17.657 16.657\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibCharacterSpacing": {
        "is_tune": True,
        "title": "DocLib Character Spacing",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M3 12H21M3 12L7 8M3 12L7 16M21 12L17 8M21 12L17 16M10 6V18M14 6V18\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibTextScaling": {
        "is_tune": True,
        "title": "DocLib Text Scaling",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M8 4H16V20H8V4ZM4 8H8M16 8H20M4 16H8M16 16H20\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibConvertTextToTable": {
        "is_block": True,
        "title": "DocLib Convert Text To Table",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 6H10M4 12H10M4 18H10M14 12H20L17 9M20 12L17 15\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibConvertTableToText": {
        "is_block": True,
        "title": "DocLib Convert Table To Text",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M20 6H14M20 12H14M20 18H14M10 12H4L7 9M4 12L7 15\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibSplitWindow": {
        "is_tune": True,
        "title": "DocLib Split Window",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><rect x=\"4\" y=\"4\" width=\"16\" height=\"16\" rx=\"2\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M4 12H20\" stroke=\"currentColor\" stroke-width=\"2\"/></svg>"
    },
    "DocLibSynchronousScrolling": {
        "is_tune": True,
        "title": "DocLib Synchronous Scrolling",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M8 4V20M16 4V20M5 7L8 4L11 7M13 17L16 20L19 17\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibOutlineView": {
        "is_tune": True,
        "title": "DocLib Outline View",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 6H20M8 12H20M12 18H20M4 12H5M8 18H9\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibDraftView": {
        "is_tune": True,
        "title": "DocLib Draft View",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 6H20M4 10H14M4 14H20M4 18H16\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg>"
    },
    "DocLibWebLayout": {
        "is_tune": True,
        "title": "DocLib Web Layout",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M3 6C3 4.89543 3.89543 4 5 4H19C20.1046 4 21 4.89543 21 6V18C21 19.1046 20.1046 20 19 20H5C3.89543 20 3 19.1046 3 18V6Z\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M3 8H21\" stroke=\"currentColor\" stroke-width=\"2\"/></svg>"
    },
    "DocLibRuler": {
        "is_tune": True,
        "title": "DocLib Ruler",
        "icon": "<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\"><path d=\"M4 6H20V12H4V6Z\" stroke=\"currentColor\" stroke-width=\"2\"/><path d=\"M6 6V9M10 6V8M14 6V9M18 6V8\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\"/></svg>"
    }
}

target_dir = "frontend/features/compilation/components"
os.makedirs(target_dir, exist_ok=True)

for name, meta in components.items():
    is_tune = meta.get("is_tune", False)
    is_inline = meta.get("inline", False)
    title = meta["title"]
    icon = meta["icon"]
    
    if is_tune:
        code = f"""import {{ API, BlockTune }} from "@editorjs/editorjs";

export default class {name} implements BlockTune {{
  static get isTune() {{
    return true;
  }}

  private api: API;
  private data: any;
  private wrapper: HTMLElement;

  constructor({{ api, data }}: {{ api: API; data: any }}) {{
    this.api = api;
    this.data = data || {{ enabled: false }};
    this.wrapper = document.createElement("div");
  }}

  render() {{
    const btn = document.createElement("button");
    btn.classList.add(this.api.styles.settingsButton);
    btn.innerHTML = `{icon}`;
    btn.dataset.title = "{title}";

    if (this.data.enabled) {{
      btn.classList.add(this.api.styles.settingsButtonActive);
    }}

    btn.addEventListener("click", () => {{
      this.data.enabled = !this.data.enabled;
      btn.classList.toggle(this.api.styles.settingsButtonActive);
    }});

    this.wrapper.appendChild(btn);
    return this.wrapper;
  }}

  save() {{
    return this.data;
  }}

  wrap(blockContent: HTMLElement) {{
    const w = document.createElement("div");
    if (this.data.enabled) {{
      w.classList.add("doclib-{name.lower()}-active");
    }}
    w.appendChild(blockContent);
    return w;
  }}
}}
"""
    elif is_inline:
        code = f"""import {{ API, InlineTool }} from "@editorjs/editorjs";

export default class {name} implements InlineTool {{
  static get isInline() {{
    return true;
  }}

  static get title() {{
    return "{title}";
  }}

  private api: API;
  private button: HTMLButtonElement | null = null;
  private tag = "SPAN";

  constructor({{ api }}: {{ api: API }}) {{
    this.api = api;
  }}

  render() {{
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.classList.add(this.api.styles.inlineToolButton);
    this.button.innerHTML = `{icon}`;
    return this.button;
  }}

  surround(range: Range) {{
    if (!range) return;
    const termWrapper = this.api.selection.findParentTag(this.tag, "{name}");
    if (termWrapper) {{
      this.unwrap(termWrapper);
    }} else {{
      this.wrap(range);
    }}
  }}

  wrap(range: Range) {{
    const el = document.createElement(this.tag);
    el.classList.add("{name}");
    el.appendChild(range.extractContents());
    range.insertNode(el);
    this.api.selection.expandToTag(el);
  }}

  unwrap(termWrapper: HTMLElement) {{
    this.api.selection.expandToTag(termWrapper);
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0) {{
      const range = sel.getRangeAt(0);
      const unwrappedContent = range.extractContents();
      termWrapper.parentNode?.removeChild(termWrapper);
      range.insertNode(unwrappedContent);
      sel.removeAllRanges();
      sel.addRange(range);
    }}
  }}

  checkState() {{
    const termWrapper = this.api.selection.findParentTag(this.tag, "{name}");
    if (this.button) {{
      this.button.classList.toggle(
        this.api.styles.inlineToolButtonActive,
        !!termWrapper
      );
    }}
    return !!termWrapper;
  }}
}}
"""
    else:
        code = f"""import {{ API, BlockTool, BlockToolData }} from "@editorjs/editorjs";

export default class {name} implements BlockTool {{
  static get toolbox() {{
    return {{
      title: "{title}",
      icon: `{icon}`,
    }};
  }}

  private api: API;
  private data: BlockToolData;
  private wrapper: HTMLElement;

  constructor({{ api, data }}: {{ api: API; data: BlockToolData }}) {{
    this.api = api;
    this.data = data || {{ content: "" }};
    this.wrapper = document.createElement("div");
  }}

  render() {{
    this.wrapper.classList.add("ce-block");
    const input = document.createElement("input");
    input.classList.add("ce-paragraph", "cdx-block");
    input.value = this.data.content || "";
    input.placeholder = "{title}";
    this.wrapper.appendChild(input);
    return this.wrapper;
  }}

  save(blockContent: HTMLElement) {{
    const input = blockContent.querySelector("input") as HTMLInputElement;
    return {{
      content: input ? input.value : "",
    }};
  }}
}}
"""
    with open(os.path.join(target_dir, f"{name}.ts"), "w", encoding="utf-8") as f:
        f.write(code)

