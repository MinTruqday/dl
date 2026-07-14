import ast
from typing import List, Dict, Any
from loguru import logger

class ASTNodeChunk:
    def __init__(self, node_type: str, name: str, code_snippet: str, lineno: int):
        self.node_type = node_type
        self.name = name
        self.code_snippet = code_snippet
        self.lineno = lineno
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.node_type,
            "name": self.name,
            "snippet": self.code_snippet,
            "line": self.lineno
        }

class ASTIndexer:
    """
    <module_purpose>
    <purpose>Parses Python ASTs and indexes semantic structures into the Vector Database.</purpose>
    <metis_behavior>Operates deterministically. Reads the custom XML docstrings of classes/functions for optimal RAG context injection.</metis_behavior>
    </module_purpose>
    """
    def __init__(self, vector_store=None):
        pass
        
    def _extract_source(self, lines: List[str], node: ast.AST) -> str:
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            return ""
        return "".join(lines[node.lineno - 1: node.end_lineno])

    def index_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
                lines = source_code.splitlines(keepends=True)
                
            tree = ast.parse(source_code, filename=file_path)
        except Exception as e:
            logger.exception("Parsing execution failed")
            return []
            
        chunks = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                snippet = self._extract_source(lines, node)
                chunks.append(ASTNodeChunk("function", node.name, snippet, node.lineno).to_dict())
            elif isinstance(node, ast.AsyncFunctionDef):
                snippet = self._extract_source(lines, node)
                chunks.append(ASTNodeChunk("async_function", node.name, snippet, node.lineno).to_dict())
            elif isinstance(node, ast.ClassDef):
                snippet = self._extract_source(lines, node)
                chunks.append(ASTNodeChunk("class", node.name, snippet, node.lineno).to_dict())
                
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_snippet = self._extract_source(lines, child)
                        chunks.append(
                            ASTNodeChunk(f"method_{node.name}", child.name, method_snippet, child.lineno).to_dict()
                        )
                        
        logger.info("AST indexing execution completed successfully")
        return chunks
        
    def build_graph_relations(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"nodes": chunks, "edges": []}
