import json
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger
from pydantic import BaseModel, Field

from src.core.registry import PromptType, registry


class MindmapBranch(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    children: list[str] = Field(min_length=1, max_length=5)


class MindmapStructure(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    branches: list[MindmapBranch] = Field(min_length=1, max_length=6)


def _build_tree(topic: str, structure: MindmapStructure | None) -> dict:
    branches = structure.branches if structure else []
    return {
        "title": structure.title if structure else topic,
        "root": {
            "id": "root",
            "name": topic,
            "children": [
                {
                    "id": f"branch-{branch_index}",
                    "name": branch.name,
                    "children": [
                        {
                            "id": f"node-{branch_index}-{child_index}",
                            "name": child,
                        }
                        for child_index, child in enumerate(branch.children, 1)
                    ],
                }
                for branch_index, branch in enumerate(branches, 1)
            ],
        },
    }


def _to_mermaid(tree: dict) -> str:
    lines = ["mindmap", f"  root(({tree['root']['name']}))"]
    for branch in tree["root"]["children"]:
        lines.append(f"    {branch['name']}")
        lines.extend(
            f"      {child['name']}"
            for child in branch.get("children", [])
        )
    return "\n".join(lines) + "\n"


@tool
async def generate_mindmap(
    topic: Annotated[str, Field(min_length=1, description="Topic or concept to organize into a hierarchical mind map")],
    config: RunnableConfig,
) -> str:
    """
    <module_purpose>
    Generate a structured interactive mind map for a topic.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use when the user asks for a mind map or concept hierarchy.
    - Labels follow the language of the supplied topic.
    - Returns structured tree and Mermaid representations.
    </contract>
    """
    structure = None
    try:
        from src.agents.planning import llm

        prompt = registry.get(PromptType.MINDMAP_GENERATION).format(topic=topic)
        structure = await llm.with_structured_output(MindmapStructure).ainvoke(prompt)
    except Exception:
        logger.exception("Mind map structure generation failed")

    tree = _build_tree(topic.strip(), structure)
    mermaid = _to_mermaid(tree)
    payload = {
        "status": "success" if structure else "degraded",
        "topic": topic,
        "tree": tree,
        "mermaid": mermaid,
    }
    return (
        f"```mermaid\n{mermaid}```\n"
        '<agentic-payload kind="MINDMAP_PAYLOAD">'
        f"{json.dumps(payload, ensure_ascii=False)}"
        "</agentic-payload>"
    )
