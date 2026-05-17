from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    chat_history: List[dict]
    question: str
    generation: str
    documents: List[str]
    retry_count: int
    hallucination_pass: str
    current_source: str
    route: str
    use_web: bool
    use_smart: bool
    user_id: str
    document_id: str
    image_data: str
    file_data: str

class CoordinatorState(TypedDict):
    req: Any
    steps: List[Dict[str, str]]
    current_step_index: int
    consolidated_results: List[str]
    final_answer: str
    next_node: str
    error: str
