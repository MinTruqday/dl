from typing import List, Literal
from pydantic import BaseModel, Field

class ContextQuery(BaseModel):
    question: str = Field(
        description="CRITICAL: The rewritten, fully self-contained version of the user's question. MUST resolve ALL pronouns (it, they, that) and implicit references into explicit subject names drawn from the conversation history."
    )

class GraphRoute(BaseModel):
    route: Literal["rag", "direct"] = Field(
        description="CRITICAL: MUST be 'rag' if the user needs factual knowledge, documents, or data retrieval. MUST be 'direct' if it's a casual conversation, greeting, or can be answered strictly from generic knowledge without external context."
    )

class RetrievalStrategy(BaseModel):
    is_simple: bool = Field(
        description="CRITICAL: Set to True ONLY if a single vector search query is sufficient to retrieve the answer. Set to False if the question is multi-part, comparative, or requires aggregating from multiple distinct topics."
    )
    queries: List[str] = Field(
        description="CRITICAL: A list of 1 to 5 highly optimized search queries. MUST be concise (3-8 keywords) and focused for vector similarity search. Do NOT use full conversational sentences."
    )

class QueryOptimization(BaseModel):
    question: str = Field(description="The optimal, search-engine-friendly query string stripped of conversational fluff.")

class RouteDecision(BaseModel):
    reasoning: str = Field(description="A short explanation (1-2 sentences) of why this specific route was chosen based on the user's intent.")
    route: Literal["action", "knowledge", "chat"] = Field(
        description="Selected route. 'action': user wants to execute tools/modify state. 'knowledge': user is asking a factual question needing RAG. 'chat': casual greeting or generic conversational filler."
    )
    answer: str = Field(default="", description="If route is 'chat', provide the direct response here. Otherwise, return an empty string.")

class MultiQueryOutput(BaseModel):
    queries: List[str] = Field(
        description="Exactly 3 diverse, distinct phrasings of the original query to maximize retrieval recall from the vector database."
    )
