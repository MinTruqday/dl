set -eu

ollama show "$LLM_MODEL" >/dev/null 2>&1 || ollama pull "$LLM_MODEL"
ollama run "$LLM_MODEL" 'Reply OK'
