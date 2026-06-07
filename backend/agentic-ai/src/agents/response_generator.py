import time
from loguru import logger
from typing import List
from src.core.prompt_registry import prompt_registry, PromptType


class ResponseGenerator:
    def __init__(self):
        pass
        
    async def aggregate_stream(self, query: str, consolidated_results: List[str]):
        logger.info(f"ResponseGenerator: Consolidating results for query: {query[:50]}")
        
        try:
            from src.agents.planning import llm
            from langchain_core.messages import HumanMessage
            
            gathered_data = "\n\n".join(consolidated_results)
            if len(gathered_data) > 12000:
                from langchain_text_splitters import RecursiveCharacterTextSplitter
                splitter = RecursiveCharacterTextSplitter(chunk_size=12000, chunk_overlap=0)
                chunks = splitter.split_text(gathered_data)
                gathered_data = chunks[0] + "\n[Nội dung đã được cắt bớt do quá dài]" if chunks else ""
                
            final_prompt = prompt_registry.get(PromptType.AGGREGATOR).format(query=query, gathered_data=gathered_data)
            
            async for chunk in llm.astream([HumanMessage(content=final_prompt)]):
                if chunk.content:
                    yield chunk.content
            
        except Exception as e:
            logger.error(f"ResponseGenerator error: {str(e)}")
            yield "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

response_generator = ResponseGenerator()