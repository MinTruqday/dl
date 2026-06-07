import operator
from typing import TypedDict, List, Dict, Any, Annotated
from langchain_core.messages import RemoveMessage

def reduce_chat_history(left: list, right: list) -> list:
    if left is None: left = []
    if right is None: right = []
    if not isinstance(left, list): left = []
    if not isinstance(right, list): right = [right]
    
    res = left.copy()
    for m in right:
        if isinstance(m, RemoveMessage):
            if res:
                res.pop(0)
        else:
            res.append(m)
            
    if len(res) > 15:
        return res[-15:]
    return res

class AgentState(TypedDict):
    chat_history: Annotated[list, reduce_chat_history]
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

class ActingState(TypedDict):
    req: Any
    steps: List[Dict[str, str]]
    current_step_index: int
    consolidated_results: Annotated[list, operator.add]
    final_answer: str
    next_node: str
    error: str
    replan_count: int
    start_time: float
