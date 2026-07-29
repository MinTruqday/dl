import hashlib
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "frontend" / "features" / "compilation" / "components"
EDITOR = COMPONENTS / "StandardEditor.tsx"
CATALOG = COMPONENTS / "word-command-catalog.ts"
MANIFEST = COMPONENTS / "word-feature-manifest.json"
BACKEND_MANIFEST = (
    ROOT
    / "backend"
    / "compilation"
    / "src"
    / "resources"
    / "word-feature-manifest.json"
)
INTERACTIVE_TYPES = {
    "button",
    "checkBox",
    "comboBox",
    "dropDown",
    "gallery",
    "labelControl",
    "menu",
    "splitButton",
    "toggleButton",
}


def spreadsheet_rows(path):
    namespace = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    with zipfile.ZipFile(path) as archive:
        strings_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        strings = [
            "".join(
                node.text or ""
                for node in item.iter(
                    "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
                )
            )
            for item in strings_root.findall("m:si", namespace)
        ]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relations = ET.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        targets = {
            relation.attrib["Id"]: relation.attrib["Target"]
            for relation in relations
        }
        sheet = workbook.find("m:sheets/m:sheet", namespace)
        relation_id = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        target = "xl/" + targets[relation_id].lstrip("/")
        sheet_root = ET.fromstring(archive.read(target))
        values = []
        for row in sheet_root.findall(".//m:sheetData/m:row", namespace):
            current = []
            for cell in row.findall("m:c", namespace):
                value_node = cell.find("m:v", namespace)
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = strings[int(value)]
                current.append(value)
            values.append(current)
    header = values[0]
    return [
        dict(zip(header, row + [""] * len(header)))
        for row in values[1:]
    ]


def unique_controls(rows):
    controls = {}
    for row in rows:
        name = row.get("Control Name", "")
        if name and name not in controls:
            controls[name] = row
    return controls


def legacy_names():
    source = EDITOR.read_text(encoding="utf-8")
    return set(re.findall(r'await import\("\./(DocLib[^"/]+)"\)', source))


def command_names():
    source = CATALOG.read_text(encoding="utf-8")
    return set(
        name
        for name, target in re.findall(
            r'^import (DocLib[A-Za-z0-9]+) from "\./(DocLib[A-Za-z0-9]+)";$',
            source,
            re.M,
        )
        if name == target
    )


def control_score(row):
    text = (
        row.get("Tab", "")
        + " "
        + row.get("Group/Context Menu Name", "")
    ).lower()
    weights = {
        "home": 50,
        "insert": 48,
        "layout": 46,
        "references": 44,
        "review": 42,
        "view": 40,
        "mailings": 38,
        "design": 36,
        "developer": 34,
        "file": 30,
    }
    score = max(
        [value for key, value in weights.items() if key in text] or [0]
    )
    if "context" in row.get("Group/Context Menu Name", "").lower():
        score -= 10
    if row.get("Control Type") == "button":
        score += 5
    return score


def select_controls(controls, existing):
    candidates = []
    for name, row in controls.items():
        if name in existing:
            continue
        if row.get("Control Type") not in INTERACTIVE_TYPES:
            continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name):
            continue
        if not row.get("Tab") and not row.get("Group/Context Menu Name"):
            continue
        candidates.append((control_score(row), name, row))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [(name, row) for _, name, row in candidates]


def category_for(row):
    text = (
        row.get("Tab", "")
        + " "
        + row.get("Group/Context Menu Name", "")
    ).lower()
    mappings = (
        ("table", "table"),
        ("review", "review"),
        ("reference", "reference"),
        ("mail", "mailing"),
        ("view", "view"),
        ("layout", "layout"),
        ("design", "format"),
        ("picture", "media"),
        ("chart", "media"),
        ("media", "media"),
        ("insert", "insert"),
        ("developer", "automation"),
    )
    for marker, category in mappings:
        if marker in text:
            return category
    return "format"


def icon_for(name):
    digest = hashlib.sha256(name.encode()).digest()
    points = []
    for index in range(0, 12, 2):
        x = 4 + digest[index] % 17
        y = 4 + digest[index + 1] % 17
        points.append(f"{x},{y}")
    color = digest[12] % 6
    return (
        '<svg width="24" height="24" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="2" '
        f'data-doclib-icon="{digest.hex()[:16]}">'
        f'<rect x="{2 + color}" y="{2 + color}" '
        f'width="{20 - color * 2}" height="{20 - color * 2}" rx="3"/>'
        f'<polyline points="{" ".join(points)}"/></svg>'
    )


def title_for(name):
    return "DocLib " + name


def feature_record(name, row, origin, tool_key=None, mode=None):
    return {
        "id": "DocLib" + name,
        "title": title_for(name),
        "icon": icon_for("DocLib" + name),
        "product": "doclib",
        "description": "DocLib editing command",
        "toolKey": tool_key,
        "mode": mode,
    }


def update_existing_file(path, record):
    source = path.read_text(encoding="utf-8")
    class_match = re.search(r"export default class\s+[A-Za-z0-9_]+[^{]*\{", source)
    if not class_match:
        raise RuntimeError(f"Default class missing in {path.name}")
    if "static readonly feature = " not in source:
        metadata = (
            "\n  static readonly feature = {\n"
            f'    id: "{record["id"]}",\n'
            f'    title: "{record["title"]}",\n'
            f"    icon: '{record['icon']}',\n"
            '    product: "doclib",\n'
            "  } as const;\n"
        )
        source = (
            source[:class_match.end()]
            + metadata
            + source[class_match.end():]
        )
    source = re.sub(
        r'    origin: "(?:microsoft-word|word-compatible|doclib-native)",',
        '    product: "doclib",',
        source,
    )
    source = re.sub(
        r"<svg\b.*?</svg>",
        record["icon"],
        source,
        flags=re.S,
    )
    source = re.sub(
        r'(\btitle:\s*")(?!(?:DocLib)\s)([^"]+)(")',
        lambda match: match.group(1) + "DocLib " + match.group(2) + match.group(3),
        source,
    )
    source = re.sub(
        r'(readonly title = ")(?!(?:DocLib)\s)([^"]+)(")',
        lambda match: match.group(1) + "DocLib " + match.group(2) + match.group(3),
        source,
    )
    source = re.sub(
        r'(return ")(?!(?:DocLib)\s)([^"]+)(";)',
        lambda match: (
            match.group(1) + "DocLib " + match.group(2) + match.group(3)
            if "title" in source[max(0, match.start() - 100):match.start()]
            else match.group(0)
        ),
        source,
    )
    path.write_text(source, encoding="utf-8")


def new_feature_source(record, row):
    identifier = record["id"]
    title = record["title"]
    icon = record["icon"]
    category = category_for(row)
    mode = record["mode"]
    return f'''import {{ API, BlockTool, BlockToolData }} from "@editorjs/editorjs";

export default class {identifier} implements BlockTool {{
  static readonly feature = {{
    id: "{identifier}",
    title: "{title}",
    icon: '{icon}',
    product: "doclib",
  }} as const;

  static get toolbox() {{
    return {{
      title: "{title}",
      icon: '{icon}',
    }};
  }}

  static get isReadOnlySupported() {{
    return true;
  }}

  readonly id = "{identifier}";
  readonly title = "{title}";
  readonly category = "{category}" as const;
  readonly mode = "{mode}";
  readonly requiresSelection = false;
  private api?: API;
  private data: BlockToolData;
  private wrapper: HTMLElement | null = null;

  constructor(
    {{ api, data }}: {{ api?: API; data?: BlockToolData }} = {{}},
  ) {{
    this.api = api;
    this.data = data || {{}};
  }}

  render() {{
    this.wrapper = document.createElement("div");
    this.wrapper.classList.add("cdx-block", "doclib-word-command");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = this.title;
    button.classList.add("doclib-word-command__button");
    button.dataset.applied = this.data.applied === true ? "true" : "false";
    button.addEventListener("click", () => {{
      if (!this.api || !this.wrapper) return;
      void this.execute(this.api)
        .then(() => {{
          if (!this.wrapper) return;
          this.wrapper.dataset.applied = "true";
          button.dataset.applied = "true";
          this.data = {{
            feature: this.id,
            mode: this.mode,
            applied: true,
          }};
        }})
        .catch((error) => {{
          if (this.wrapper) {{
            this.wrapper.dataset.error =
              error instanceof Error ? error.message : "Command failed";
          }}
        }});
    }});
    this.wrapper.appendChild(button);
    return this.wrapper;
  }}

  save(blockContent: HTMLElement) {{
    return {{
      feature: this.id,
      mode: this.mode,
      applied: blockContent.dataset.applied === "true",
    }};
  }}

  validate(savedData: BlockToolData) {{
    return savedData.feature === this.id && savedData.mode === this.mode;
  }}

  async execute(editor: any) {{
    const event = new CustomEvent("doclib-editor-command", {{
      cancelable: true,
      detail: {{
        command: this.id,
        mode: this.mode,
        editor,
      }},
    }});
    window.dispatchEvent(event);
    if (!event.defaultPrevented) {{
      throw new Error(`No handler registered for ${{this.id}}`);
    }}
  }}
}}
'''


def write_catalog(names):
    ordered = sorted(names)
    spread = "." * 3
    imports = "\n".join(
        f'import {name} from "./{name}";' for name in ordered
    )
    entries = "\n".join(
        f"wordCommandClasses.push({name});" for name in ordered
    )
    source = f'''import type {{ WordCommand }} from "./word-command-engine";
{imports}

type WordCommandConstructor = new ({spread}args: any[]) => WordCommand;

const wordCommandClasses: WordCommandConstructor[] = [];
{entries}

export const WORD_COMMAND_CLASSES: ReadonlyArray<WordCommandConstructor> =
  Object.freeze(wordCommandClasses);

export const WORD_COMMANDS = Object.freeze(
  WORD_COMMAND_CLASSES.map((CommandClass) => new CommandClass()),
);

export const WORD_COMMAND_TOOLS = Object.freeze(
  Object.fromEntries(
    WORD_COMMAND_CLASSES.map((CommandClass) => {{
      const command = new CommandClass();
      const name = command.mode.charAt(0).toLowerCase() + command.mode.slice(1);
      return [name, CommandClass];
    }}),
  ),
);

export const WORD_COMMAND_COUNT = WORD_COMMANDS.length;

if (
  WORD_COMMAND_COUNT !== {len(ordered)} ||
  new Set(WORD_COMMANDS.map((command) => command.id)).size !== {len(ordered)}
) {{
  throw new Error("Word command catalog must contain {len(ordered)} unique commands");
}}
'''
    CATALOG.write_text(source, encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("wordcontrols.xlsx path required")
    spreadsheet_path = pathlib.Path(sys.argv[1])
    rows = spreadsheet_rows(spreadsheet_path)
    controls = unique_controls(rows)
    legacy = legacy_names()
    commands = command_names()
    existing = legacy | commands
    if len(existing) < 500:
        raise SystemExit(f"Expected at least 500 existing features and found {len(existing)}")
    selected = select_controls(
        controls,
        {name.removeprefix("DocLib") for name in existing},
    )
    records = []
    for class_name in sorted(existing):
        name = class_name.removeprefix("DocLib")
        row = controls.get(name)
        if row:
            origin = "microsoft-word"
        elif class_name in commands:
            origin = "word-compatible"
        else:
            origin = "doclib-native"
        feature_source = (
            COMPONENTS / f"{class_name}.ts"
        ).read_text(encoding="utf-8")
        mode_match = re.search(
            r'readonly mode = "([^"]+)"',
            feature_source,
        )
        tool_key = None
        if mode_match and class_name in commands:
            mode = mode_match.group(1)
            tool_key = mode[:1].lower() + mode[1:]
        record = feature_record(
            name,
            row,
            origin,
            tool_key,
            mode_match.group(1) if mode_match else None,
        )
        update_existing_file(COMPONENTS / f"{class_name}.ts", record)
        records.append(record)
    for name, row in selected:
        record = feature_record(
            name,
            row,
            "microsoft-word",
            name[:1].lower() + name[1:],
            name,
        )
        path = COMPONENTS / f"{record['id']}.ts"
        if path.exists():
            raise SystemExit(f"Feature already exists {path.name}")
        path.write_text(new_feature_source(record, row), encoding="utf-8")
        commands.add(record["id"])
        records.append(record)
    records.sort(key=lambda record: record["id"])
    manifest_content = (
        json.dumps(
            {
                "schemaVersion": 1,
                "features": records,
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    MANIFEST.write_text(manifest_content, encoding="utf-8")
    BACKEND_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    BACKEND_MANIFEST.write_text(manifest_content, encoding="utf-8")
    write_catalog(commands)
    print(
        json.dumps(
            {
                "features": len(records),
                "legacy": len(legacy),
                "commands": len(commands),
                "newCommands": len(selected),
            }
        )
    )


if __name__ == "__main__":
    main()
