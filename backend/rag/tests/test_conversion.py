from pathlib import Path

from src.services.conversion import ConversionService


class FakeItem:
    def __init__(self, text, label):
        self.text = text
        self.label = type("Label", (), {"value": label})()
        self.prov = []


class FakeDocument:
    pages = {1: object(), 2: object()}

    @staticmethod
    def export_to_markdown():
        return "# Docling\n\nNội dung tài liệu đã được chuyển đổi."

    @staticmethod
    def iterate_items():
        yield FakeItem("Docling", "section_header"), 0
        yield FakeItem("Nội dung tài liệu đã được chuyển đổi.", "text"), 1


class FakeConverter:
    @staticmethod
    def convert(_file_path):
        return type("Conversion", (), {"document": FakeDocument()})()


def test_conversion_returns_markdown_and_docling_structure_only(monkeypatch):
    service = ConversionService()
    monkeypatch.setattr(service, "_get_docling", lambda: FakeConverter())

    parsed = service._parse_file(Path("document.pdf"))

    assert parsed["markdown"].startswith("# Docling")
    assert parsed["page_count"] == 2
    assert parsed["structure"] == [
        {"text": "Docling", "type": "section_header", "level": 0, "page_no": None},
        {
            "text": "Nội dung tài liệu đã được chuyển đổi.",
            "type": "text",
            "level": 1,
            "page_no": None,
        },
    ]
    assert "chunks" not in parsed


def test_conversion_preserves_markdown_when_structure_extraction_fails(monkeypatch):
    service = ConversionService()
    monkeypatch.setattr(service, "_get_docling", lambda: FakeConverter())

    def unavailable_structure(_document):
        raise RuntimeError("structure unavailable")

    monkeypatch.setattr(service, "_extract_structure", unavailable_structure)
    parsed = service._parse_file(Path("document.pdf"))

    assert parsed["markdown"].startswith("# Docling")
    assert parsed["structure"] == []
