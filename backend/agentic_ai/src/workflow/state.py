import operator
from typing import Annotated, Any, Dict, List, TypedDict

from langchain_core.messages import BaseMessage, RemoveMessage, SystemMessage

def reduce_chat_history(left: list, right: list) -> list:
    if left is None:
        left = []
    if right is None:
        right = []
    if not isinstance(left, list):
        left = []
    if not isinstance(right, list):
        right = [right]

    res = left.copy()
    for m in right:
        if isinstance(m, RemoveMessage):
            if res:
                res.pop(0)
        else:
            res.append(m)

    recent_msgs = []
    for m in res:
        if isinstance(m, SystemMessage):
            recent_msgs.append(m)
        else:
            content = str(m.content)
            if len(content) > 1500:
                m.content = f"{content[:500]}\n[REDACTED COMPRESSED CONTENT]\n{content[-500:]}"
            recent_msgs.append(m)
            
    if len(recent_msgs) > 15:
        system_msgs = [m for m in recent_msgs if isinstance(m, SystemMessage)]
        other_msgs = [m for m in recent_msgs if not isinstance(m, SystemMessage)]
        recent_msgs = system_msgs + other_msgs[-(15 - len(system_msgs)):] if len(system_msgs) < 15 else system_msgs

    return recent_msgs

def reduce_consolidated_results(left: list, right: list) -> list:
    if left is None:
        left = []
    if right is None:
        right = []
    if not isinstance(left, list):
        left = []
    if not isinstance(right, list):
        right = [right]

    combined = left + right
    if len(combined) > 15:
        combined = [combined[0]] + combined[-14:]
    return combined

class AgentState(TypedDict):
    """
    <module_purpose>
    DocLib Agent State defining the graph state schema for the primary RAG and Agentic workflow.
    </module_purpose>
    <contract>
    - Precondition: Initialized at the start of the LangGraph execution.
    - Postcondition: Accumulates messages, search results, and execution metadata.
    - Error Handling: Uses custom reducers to prevent memory bloat and context limit exhaustion.
    </contract>
    """
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
    document_ids: list
    image_data: str
    file_data: str
    folder_data: str
    thread_id: str
    current_node: str
    artifacts: Dict[str, Any]
    dynamic_injections: List[Any]

class ActingState(TypedDict):
    """
    <module_purpose>
    DocLib Acting State defining the minimal state payload for Tool execution graphs.
    </module_purpose>
    <contract>
    - Precondition: Tool execution requests containing req_data.
    - Postcondition: Persists data across execution nodes.
    - Error Handling: Relies on external validators before state instantiation.
    </contract>
    """
    req_data: Dict[str, Any]
    steps: List[Any]
    current_step_index: int
    completed_tasks: list
    task_status: Dict[str, str]
    consolidated_results: Annotated[list, reduce_consolidated_results]
    final_answer: str
    next_nodes: List[str]
    error: str
    replan_count: int
    start_time: float
    artifacts: Dict[str, Any]
    dynamic_injections: List[Any]
    results_trimmed: bool
    execution_history: List[Any]
