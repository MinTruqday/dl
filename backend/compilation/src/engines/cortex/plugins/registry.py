from src.engines.cortex.plugins.core_blocks import ParagraphTranslator, HeadingTranslator, RawTranslator
from src.engines.cortex.plugins.containers import ContainerTranslator
from src.engines.cortex.plugins.math_code import MathTranslator, CodeTranslator
from src.engines.cortex.plugins.media_table import TableTranslator, ImageTranslator
from src.engines.cortex.plugins.academic import ListTranslator, CiteTranslator, RefTranslator, BibliographyTranslator

TRANSLATOR_REGISTRY = {
    "paragraph": ParagraphTranslator,
    "h1": HeadingTranslator,
    "h2": HeadingTranslator,
    "h3": HeadingTranslator,
    "raw": RawTranslator,
    "latex": RawTranslator,
    "note": ContainerTranslator,
    "warn": ContainerTranslator,
    "info": ContainerTranslator,
    "math": MathTranslator,
    "code": CodeTranslator,
    "img": ImageTranslator,
    "tbl": TableTranslator,
    "list": ListTranslator,
    "enum": ListTranslator,
    "cite": CiteTranslator,
    "ref": RefTranslator,
    "bibliography": BibliographyTranslator,
}
