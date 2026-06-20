import os
import re

file_moves = {
    "agentic_ai/src/agents/action.py": "agentic_ai/src/agents/actor.py",
    "agentic_ai/src/agents/reasoning.py": "agentic_ai/src/agents/reasoner.py",
    "agentic_ai/src/agents/knowledge.py": "agentic_ai/src/agents/researcher.py",
    "agentic_ai/src/agents/planning.py": "agentic_ai/src/agents/planner.py",
    "agentic_ai/src/store/vector_store.py": "agentic_ai/src/store/vector.py",
    "agentic_ai/src/training/engine.py": "agentic_ai/src/training/trainer.py",
    "agentic_ai/src/rag/retrieval.py": "agentic_ai/src/rag/retriever.py",
    "agentic_ai/src/rag/document_parser.py": "agentic_ai/src/rag/parser.py",
    "agentic_ai/src/rag/ingestion_pipeline.py": "agentic_ai/src/rag/pipeline.py",
    "realtime/src/services/editor_ws.py": "realtime/src/services/editor_socket.py",
    "realtime/src/services/message_ws.py": "realtime/src/services/message_socket.py",
    "realtime/src/router/editor_ws.py": "realtime/src/router/editor_socket.py",
    "realtime/src/router/message_ws.py": "realtime/src/router/message_socket.py",
}

for old, new in file_moves.items():
    if os.path.exists(old):
        os.rename(old, new)
        print(f"Moved {old} -> {new}")

# Now global content replacements
replacements = [
    (r"\bsrc\.agents\.action\b", "src.agents.actor"),
    (r"\bsrc\.agents\.reasoning\b", "src.agents.reasoner"),
    (r"\bsrc\.agents\.knowledge\b", "src.agents.researcher"),
    (r"\bsrc\.agents\.planning\b", "src.agents.planner"),
    (r"\bsrc\.store\.vector_store\b", "src.store.vector"),
    (r"\bsrc\.training\.engine\b", "src.training.trainer"),
    (r"\bsrc\.rag\.retrieval\b", "src.rag.retriever"),
    (r"\bsrc\.rag\.document_parser\b", "src.rag.parser"),
    (r"\bsrc\.rag\.ingestion_pipeline\b", "src.rag.pipeline"),
    (r"\bsrc\.services\.editor_ws\b", "src.services.editor_socket"),
    (r"\bsrc\.services\.message_ws\b", "src.services.message_socket"),
    (r"\bsrc\.router\.editor_ws\b", "src.router.editor_socket"),
    (r"\bsrc\.router\.message_ws\b", "src.router.message_socket"),
    # Classes
    (r"class Actor(\s*:|\()", r"class Actor\1"),
    (r"class Reasoner(\s*:|\()", r"class Reasoner\1"),
    (r"class Researcher(\s*:|\()", r"class Researcher\1"),
    (r"class Planner(\s*:|\()", r"class Planner\1"),
    (r"class VectorDatabase(\s*:|\()", r"class VectorDatabase\1"),
    (r"class Retriever(\s*:|\()", r"class Retriever\1"),
    (r"class Embedder(\s*:|\()", r"class Embedder\1"),
    (r"class FileParser(\s*:|\()", r"class FileParser\1"),
    # agentic_ai specific instances
    (r"\baction = Action\(\)", "actor = Actor()"),
    (r"\breasoning = Reasoning\(\)", "reasoner = Reasoner()"),
    (r"\bknowledge = Knowledge\(\)", "researcher = Researcher()"),
    (r"\bplanning = Planning\(\)", "planner = Planner()"),
    (r"\bretrieval_service = RetrievalManager\(\)", "retriever = Retriever()"),
    (r"\bembedding_service = EmbeddingManager\(\)", "embedder = Embedder()"),
    # instance usage in supervisor.py and others
    (r"from src\.agents\.executor import action", "from src.agents.actor import actor"),
    (
        r"from src\.agents\.reasoner import reasoning",
        "from src.agents.reasoner import reasoner",
    ),
    (
        r"from src\.agents\.researcher import knowledge",
        "from src.agents.researcher import researcher",
    ),
    (
        r"from src\.agents\.planner import planning",
        "from src.agents.planner import planner",
    ),
    (r"\baction\.execute\(", "actor.execute("),
    (r"\breasoning\.execute\(", "reasoner.execute("),
    (r"\bknowledge\.execute\(", "researcher.execute("),
    (r"\bplanning\.execute\(", "planner.execute("),
    (r"\bplanning\.create_plan\(", "planner.create_plan("),
    (r"\baction_agent_node", "actor_agent_node"),
    (r"\breasoning_agent_node", "reasoner_agent_node"),
    (r"\bknowledge_agent_node", "researcher_agent_node"),
    (
        r"from src\.rag\.retriever import retrieval_service",
        "from src.rag.retriever import retriever",
    ),
    (
        r"from src\.rag\.embedder import embedding_service",
        "from src.rag.embedder import embedder",
    ),
    (r"\bretrieval_service\.", "retriever."),
    (r"\bembedding_service\.", "embedder."),
    # realtime websocket renaming
    (r"class EditorSocketManager(\s*:|\()", r"class EditorSocketManager\1"),
    (r"class MessageSocketManager(\s*:|\()", r"class MessageSocketManager\1"),
    (
        r"\bmanager = ConnectionManager\(\)",
        "editor_socket_manager = EditorSocketManager()",
    ),
    (
        r"\bmanager = MessageConnectionManager\(\)",
        "message_socket_manager = MessageSocketManager()",
    ),
    (
        r"\bmanager\.",
        "editor_socket_manager.",
    ),  # In editor_ws router, manager was used.
    # in realtime/src/router/message_ws.py it might use manager or message_manager. We'll manually check it after.
]

for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                new_content = content
                for pattern, repl in replacements:
                    new_content = re.sub(pattern, repl, new_content)

                # Special targeted replacement for editor_socket_manager. in realtime
                if "realtime/src/router/message_socket.py" in path:
                    new_content = new_content.replace(
                        "editor_socket_manager.", "message_socket_manager."
                    )
                    new_content = new_content.replace(
                        "from src.services.message_socket import manager",
                        "from src.services.message_socket import message_socket_manager",
                    )

                if "realtime/src/router/editor_socket.py" in path:
                    new_content = new_content.replace(
                        "from src.services.editor_socket import manager",
                        "from src.services.editor_socket import editor_socket_manager",
                    )

                if new_content != content:
                    with open(path, "w", encoding="utf-8") as file:
                        file.write(new_content)
                    print(f"Updated {path}")
            except Exception as e:
                pass
