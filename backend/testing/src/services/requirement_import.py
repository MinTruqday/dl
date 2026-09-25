import csv
import hashlib
import io
import json
import re
import zipfile

from defusedxml import ElementTree
from pypdf import PdfReader

from src.services.domain_policy import domain_policy
from src.services.requirement_workflow import text_doc


def requirement_import_policy():
    return domain_policy("requirement_import")


def supported_requirement_formats():
    return set(requirement_import_policy()["supported_formats"])


def safe_requirement_filename(value: str, fallback: str = "source.bin") -> str:
    filename = re.sub(
        requirement_import_policy()["safe_filename_pattern"], "_", value or fallback
    )
    return filename or fallback


def parse_requirement_import(content, format):
    policy = requirement_import_policy()
    if format in set(policy["api_artifact_formats"]):
        value = json.loads(content) if isinstance(content, str) else content
        return parse_api_artifact(value, format)
    if format == "csv":
        rows = list(csv.DictReader(io.StringIO(str(content))))
        return [
            {
                "requirement_key": row.get("requirement_key") or None,
                "title": row.get("title") or f"Requirement nhập dòng {index + 1}",
                "type": row.get("type") or "functional",
                "priority": row.get("priority") or "medium",
                "risk": row.get("risk") or "medium",
                "content_doc": text_doc(row.get("content") or row.get("description") or ""),
                "acceptance_criteria": [],
            }
            for index, row in enumerate(rows)
        ]
    text = str(content)
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    return [
        {
            "title": block.splitlines()[0][: policy["maximum_title_characters"]],
            "content_doc": text_doc(block),
            "acceptance_criteria": [],
        }
        for block in blocks[: policy["maximum_text_candidates"]]
    ]


def atomic_requirement_candidates(document):
    policy = requirement_import_policy()
    content = document["normalized_content"]
    if document["format"] in set(policy["atomic_structured_formats"]):
        candidates = parse_requirement_import(content, document["format"])
        for index, candidate in enumerate(candidates):
            candidate["source_refs"] = [
                {
                    "requirement_document_id": document["_id"],
                    "content_hash": document["content_hash"],
                    "candidate_index": index,
                    "format": document["format"],
                }
            ]
            candidate["extraction_confidence"] = policy[
                "structured_extraction_confidence"
            ]
        return candidates
    text = str(content).replace("\r\n", "\n").replace("\r", "\n")
    matches = list(re.finditer(policy["sentence_pattern"], text))
    candidates = []
    for match in matches:
        raw = match.group(0)
        value = re.sub(policy["list_prefix_pattern"], "", raw).strip()
        if len(value) < 2:
            continue
        source_start = match.start() + raw.find(value)
        source_end = source_start + len(value)
        candidates.append(
            {
                "title": value[: policy["maximum_title_characters"]],
                "content_doc": text_doc(value),
                "acceptance_criteria": [],
                "source_refs": [
                    {
                        "requirement_document_id": document["_id"],
                        "content_hash": document["content_hash"],
                        "source_start": source_start,
                        "source_end": source_end,
                        "source_text_hash": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                        "format": document["format"],
                    }
                ],
                "extraction_confidence": policy["text_extraction_confidence"],
            }
        )
        if len(candidates) == policy["maximum_text_candidates"]:
            break
    return candidates


def extract_file_content(data, format):
    if format == "pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if format == "docx":
        return extract_docx(data)
    if format == "xlsx":
        return extract_xlsx_csv(data)
    text = data.decode("utf-8-sig")
    if format in set(requirement_import_policy()["api_artifact_formats"]):
        return json.loads(text)
    return text


def extract_docx(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = []
    for paragraph in root.iter(f"{namespace}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t")).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def extract_xlsx_csv(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = set(archive.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.iter() if node.tag.endswith("}t"))
                for item in root
            ]
        sheets = sorted(
            name
            for name in names
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        )
        rows = []
        for sheet in sheets:
            root = ElementTree.fromstring(archive.read(sheet))
            for row in (node for node in root.iter() if node.tag.endswith("}row")):
                values = []
                for cell in (node for node in row if node.tag.endswith("}c")):
                    cell_type = cell.attrib.get("t")
                    if cell_type == "inlineStr":
                        value = "".join(
                            node.text or "" for node in cell.iter() if node.tag.endswith("}t")
                        )
                    else:
                        value_node = next((node for node in cell if node.tag.endswith("}v")), None)
                        value = value_node.text if value_node is not None else ""
                    if cell_type == "s" and value:
                        value = shared[int(value)]
                    values.append(value or "")
                rows.append(values)
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerows(rows)
    return stream.getvalue()


def parse_api_artifact(value, artifact_format):
    policy = requirement_import_policy()
    items = []
    if artifact_format == "openapi":
        for path, operations in value.get("paths", {}).items():
            for method, operation in operations.items():
                if method.lower() not in set(policy["api_methods"]):
                    continue
                items.append(
                    {
                        "title": operation.get("summary") or f"{method.upper()} {path}",
                        "type": "api",
                        "content_doc": text_doc(
                            json.dumps(
                                {
                                    "path": path,
                                    "method": method,
                                    "parameters": operation.get("parameters", []),
                                    "responses": operation.get("responses", {}),
                                    "security": operation.get("security", []),
                                },
                                ensure_ascii=False,
                            )
                        ),
                        "source_refs": [{"type": "openapi", "path": path, "method": method}],
                        "acceptance_criteria": [],
                    }
                )
    else:
        def walk(nodes, folder=""):
            for node in nodes:
                if "item" in node:
                    walk(node["item"], "/".join(filter(None, [folder, node.get("name", "")])))
                elif "request" in node:
                    request = node["request"]
                    url = request.get("url", {})
                    raw_url = url.get("raw", "") if isinstance(url, dict) else str(url)
                    items.append(
                        {
                            "title": node.get("name")
                            or f"{request.get('method', policy['default_api_method'])} {raw_url}",
                            "type": "api",
                            "content_doc": text_doc(
                                json.dumps(
                                    {
                                        "folder": folder,
                                        "method": request.get("method"),
                                        "url_template": raw_url.split("?", 1)[0],
                                        "header_names": [
                                            header.get("key")
                                            for header in request.get("header", [])
                                        ],
                                    },
                                    ensure_ascii=False,
                                )
                            ),
                            "source_refs": [{"type": "postman", "folder": folder}],
                            "acceptance_criteria": [],
                        }
                    )

        walk(value.get("item", []))
    return items[: policy["maximum_api_candidates"]]
