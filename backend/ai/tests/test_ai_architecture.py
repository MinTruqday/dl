import ast
import unittest
from pathlib import Path


AI_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = AI_ROOT / "src"


class AIArchitectureTests(unittest.TestCase):
    def test_knowledge_is_not_a_nested_service(self):
        self.assertFalse((SOURCE_ROOT / "knowledge").exists())
        self.assertFalse((AI_ROOT / "knowledge-requirements.txt").exists())

    def test_agent_runtime_is_grouped_under_agents(self):
        for group in ("harness", "loop", "memory", "workflow"):
            self.assertFalse((SOURCE_ROOT / group).exists())
            self.assertTrue((SOURCE_ROOT / "agents" / group).is_dir())

    def test_internal_imports_resolve(self):
        missing = []
        for path in SOURCE_ROOT.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                module = node.module or ""
                if not module.startswith("src."):
                    continue
                candidate = AI_ROOT.joinpath(*module.split("."))
                if not candidate.with_suffix(".py").exists() and not (
                    candidate / "__init__.py"
                ).exists():
                    missing.append(f"{path.relative_to(AI_ROOT)}:{node.lineno} {module}")
        self.assertEqual([], missing)

    def test_old_module_names_are_absent(self):
        stale = []
        old_names = (
            "src.knowledge",
            "src.harness",
            "src.loop",
            "src.memory",
            "src.workflow",
        )
        for path in SOURCE_ROOT.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            if any(name in source for name in old_names):
                stale.append(str(path.relative_to(AI_ROOT)))
        self.assertEqual([], stale)

    def test_services_do_not_call_api_modules(self):
        invalid = []
        for path in (SOURCE_ROOT / "services").glob("*.py"):
            source = path.read_text(encoding="utf-8")
            if "from src.api" in source or "import src.api" in source:
                invalid.append(path.name)
        self.assertEqual([], invalid)


if __name__ == "__main__":
    unittest.main()
