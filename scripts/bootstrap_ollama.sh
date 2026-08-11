set -eu
ollama pull "$LLM_MODEL"
ollama run "$LLM_MODEL" "Reply with only OK" >/dev/null
