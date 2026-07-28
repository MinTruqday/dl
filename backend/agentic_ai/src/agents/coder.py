import ast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from loguru import logger

from src.agents.swarm import SwarmState
from src.core.registry import PromptType, registry
from src.schemas.coder import CoderOutput


class CoderAgent:
    """
    <module_purpose>
    DocLib Coder Agent for generating robust Python code within a Multi-Agent Swarm.
    </module_purpose>
    <contract>
    - Precondition: Receives a validated task from the Swarm Supervisor.
    - Postcondition: Returns executable code and an explanation.
    - Error Handling: Refuses to generate malware. Delegates via [SPAWN:role] if a specialized sub-agent is required.
    </contract>
    """

    def __init__(self, llm):
        self.llm = llm

    def _verify_code(self, code: str, language: str) -> str:
        if not code.strip():
            return "Generated code is empty"
        if language.lower() not in {"python", "py"}:
            return ""
        try:
            ast.parse(code)
            compile(code, "<generated-code>", "exec")
            return ""
        except (SyntaxError, ValueError, TypeError) as exc:
            return f"Static code validation failed with {type(exc).__name__}"

    async def execute(self, state: SwarmState) -> SwarmState:
        logger.info("Coder execution started via LLM")

        task = state.task
        if task.startswith("[SPAWN:"):
            end_bracket = task.find("]")
            if end_bracket > 7:
                role = task[7:end_bracket]
                spawn_task = task[end_bracket + 1:].strip()
                from src.agents.spawner import AgentSpawner
                spawner = AgentSpawner(self.llm)
                result = await spawner.spawn(role, spawn_task)
                state.messages.append(AIMessage(content=f"Spawned agent '{role}' completed task"))
                state.artifacts["code"] = result
                state.current_agent = "supervisor"
                return state

        system_prompt = registry.get(PromptType.SWARM_CODER)
        human_msg_content = f"Task: {task}\nContext: {state.context}"
        state.artifacts.pop("review", None)
        state.artifacts.pop("review_approved", None)
        state.artifacts.pop("security_report", None)
        state.artifacts.pop("security_approved", None)

        try:
            structured_llm = self.llm.with_structured_output(CoderOutput)
            
            max_retries = 2
            final_code = ""
            final_logic = ""
            
            for attempt in range(max_retries + 1):
                messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_msg_content)]
                response = await structured_llm.ainvoke(messages)
                
                final_code = response.code
                final_logic = response.logic_explanation
                
                verification_error = self._verify_code(
                    final_code,
                    response.language,
                )
                if not verification_error:
                    logger.info("Coder verification passed")
                    break
                    
                logger.warning(f"Coder verification failed on attempt {attempt+1}: {verification_error[:100]}")
                if attempt < max_retries:
                    human_msg_content += f"\n\nYour previous code failed with this error:\n{verification_error}\nPlease fix the code."
                
            response_content = f"Implementation generated.\nExplanation: {final_logic}"
            state.messages.append(AIMessage(content=response_content))
            state.artifacts["code"] = final_code
            logger.info("Coder execution completed")
        except Exception:
            logger.exception("Coder LLM generation failed")
            state.messages.append(AIMessage(content="LLM generation failed"))

        state.current_agent = "supervisor"
        return state
