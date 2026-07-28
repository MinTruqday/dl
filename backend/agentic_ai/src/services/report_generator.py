from typing import Dict, List, Optional
from loguru import logger
from src.rag.conversion import document_parser

class ExecutiveReportGenerator:
    async def generate_report_from_url(self, file_url: str) -> Dict[str, str]:
        logger.info("Generating executive report from document URL")
        parsed = await document_parser.parse_document(file_url)
        if parsed.get("error"):
            return {"error": parsed.get("error"), "report": ""}

        markdown = parsed.get("markdown", "")
        chunks = parsed.get("chunks", [])
        page_count = parsed.get("page_count", 1)

        report = self.build_report_markdown(file_url, markdown, chunks, page_count)
        return {
            "file_url": file_url,
            "report": report,
            "page_count": str(page_count),
            "chunk_count": str(len(chunks))
        }

    async def generate_report(self, title: str, chunks: List[Dict]) -> str:
        return self.build_report_markdown(title, "", chunks, 1)

    def build_report_markdown(self, title: str, markdown: str, chunks: List[Dict], page_count: int) -> str:
        headings = []
        tables = []
        text_samples = []

        for c in chunks:
            ctype = c.get("chunk_type", "text")
            text = c.get("text", "").strip()
            if ctype == "heading":
                headings.append(text)
            elif ctype == "table":
                tables.append(text)
            else:
                if len(text_samples) < 5 and len(text) > 30:
                    text_samples.append(text)

        lines = []
        lines.append("# EXECUTIVE DOCUMENT SUMMARY REPORT")
        lines.append(f"Source Document: {title}")
        lines.append(f"Total Pages Analyzed: {page_count}")
        lines.append(f"Total Structural Segments: {len(chunks)}")
        lines.append("")
        lines.append("## 1. KEY DOCUMENT HIGHLIGHTS")
        if text_samples:
            for s in text_samples:
                clean_sample = s.replace("\n", " ")
                lines.append(f"- {clean_sample[:200]}")
        else:
            lines.append("- Document content extracted successfully.")

        lines.append("")
        lines.append("## 2. STRUCTURAL OUTLINE & HEADINGS")
        if headings:
            for h in headings:
                lines.append(f"- {h}")
        else:
            lines.append("- No explicit markdown headings detected.")

        lines.append("")
        lines.append("## 3. EXTRACTED DATA TABLES")
        lines.append(f"Total Data Tables Identified: {len(tables)}")
        if tables:
            for i, tbl in enumerate(tables[:3]):
                lines.append(f"### Table {i + 1}")
                lines.append(tbl[:500])

        return "\n".join(lines)

executive_report_generator = ExecutiveReportGenerator()
