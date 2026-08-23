from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class StructuredRouting(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContextQuery(StructuredRouting):
    question: str = Field(
        description="<critical_instructions>The rewritten, fully self-contained version of the user's question. Metis MUST resolve ALL pronouns (it, they, that) and implicit references into explicit subject names drawn from the conversation history.</critical_instructions>"
    )


class GraphRoute(StructuredRouting):
    route: Literal["rag", "direct"] = Field(
        description="<critical_instructions>MUST be 'rag' if the user needs factual knowledge, documents, or data retrieval. MUST be 'direct' if it's a casual conversation, greeting, or can be answered strictly from generic knowledge without external context.</critical_instructions>"
    )


class RetrievalStrategy(StructuredRouting):
    is_simple: bool = Field(
        description="<critical_instructions>Set to True ONLY if a single vector search query is sufficient to retrieve the answer. Set to False if the question is multi-part, comparative, or requires aggregating from multiple distinct topics.</critical_instructions>"
    )
    queries: List[str] = Field(
        description="<constraints>A list of 1 to 5 highly optimized search queries. MUST be concise (3-8 keywords) and focused for vector similarity search. Do NOT use full conversational sentences.</constraints>"
    )


class QueryOptimization(StructuredRouting):
    question: str = Field(
        description="<input_context>The optimal, search-engine-friendly query string stripped of conversational fluff.</input_context>"
    )


class RouteDecision(StructuredRouting):
    reasoning: str = Field(
        description="<routing_logic>A concise route justification without private reasoning.</routing_logic>"
    )
    route: Literal["action", "knowledge", "chat"] = Field(
        description="<routing_logic>Selected route. 'action': execute tools/modify state. 'knowledge': factual question needing RAG. 'chat': casual greeting or generic conversational filler.</routing_logic>"
    )
    answer: str = Field(
        default="",
        description="<conditional_output>If route is 'chat', provide the direct response here. Otherwise, return an empty string.</conditional_output>",
    )


class MultiQueryOutput(StructuredRouting):
    queries: List[str] = Field(
        description="<critical_instructions>Exactly 3 diverse, distinct phrasings of the original query to maximize retrieval recall from the vector database.</critical_instructions>"
    )


class CrossDocumentQueries(StructuredRouting):
    queries: List[str] = Field(
        min_length=2,
        max_length=100,
        description="<critical_instructions>One focused retrieval query for each supplied document in the original document order.</critical_instructions>",
    )
