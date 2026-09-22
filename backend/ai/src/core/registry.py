from enum import Enum

from src.prompts.catalog import PROMPTS


class PromptType(str, Enum):
    PROMPT_INJECTION_DETECTOR = "prompt_injection_detector"
    SECURITY_SCAN = "security_scan"
    MULTI_QUERY = "multi_query"
    CROSS_DOCUMENT_QUERY = "cross_document_query"
    HYDE_GENERATION = "hyde_generation"
    DOCUMENT_GLOBAL_SUMMARY = "document_global_summary"
    EVAL_JUDGE = "eval_judge"
    EVALUATION_HARNESS_PROMPT = "evaluation_harness_prompt"


class PromptRegistry:
    def get(self, prompt_type: PromptType):
        return PROMPTS[prompt_type.value]

    def get_base(self, prompt_type: PromptType):
        return self.get(prompt_type)


registry = PromptRegistry()
