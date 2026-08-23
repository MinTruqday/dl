import operator
from typing import Annotated, List, TypedDict

class MapReduceState(TypedDict):
    """
    Maintains the chunking and aggregation state for the Metis long-document summarizer.
    Constraint: Enforces batch limits explicitly to prevent out-of-memory errors on massive texts.
    """
    document_text: str
    chunks: List[str]
    summaries: Annotated[list, operator.add]
    final_summary: str
