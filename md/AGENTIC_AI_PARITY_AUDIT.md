# Agentic AI parity audit

## Scope

This audit compares the DocLib agent runtime with the local Anthropic Fable 5 and Claude Code Fable 5 prompt snapshots and with current public OpenAI agent prompting guidance

Prompt length is not a capability metric

The DocLib prompt registry contains about 19,000 words while the local Claude Code Fable 5 snapshot contains about 20,000 words and the general Claude Fable 5 snapshot contains about 33,000 words

## Current strengths

DocLib has authenticated tool execution, an execution DAG, dependency-aware parallel work, planning and replanning, explicit approval records, persistent workspaces, short-term and long-term memory, retrieval, a code sandbox, web search routing, user-owned MCP connectors, output verification, security scanning and trace collection

These are real runtime components rather than prompt-only declarations

## Gaps fixed in this change

The system execution contract now defines completion evidence, instruction trust boundaries, safe autonomy, approval denial behavior, dependency ordering, retry limits, stopping conditions and honest final reporting

The ordinary and streaming chat APIs now load the same history and user preferences and persist successful exchanges through the same path

The active tool harness now registers and executes all model-visible tools and records real duration and success data

Mutating and MCP tools are not automatically retried after an unknown execution outcome

Every model-visible tool argument now has a schema description

MCP tool descriptions now state discovery prerequisites, ownership boundaries, return behavior and failure behavior

Every OpenAPI operation now has a description

The primary router no longer requests an invalid `rag` route

The dispatcher can report that no suitable tool exists instead of selecting an unrelated tool

## Remaining blockers to verified frontier parity

### Model capability

The configured generation model is `Qwen/Qwen3.6-27B`

Prompt changes cannot establish reasoning, coding, vision, instruction-following or tool-use parity with a frontier ChatGPT or Claude model

Model parity requires controlled evaluations against the exact candidate models under the same tasks, tools, context and latency limits

### Agent trajectory evaluation

The existing benchmark primarily measures answer overlap and an optional language-model judge

It does not yet grade tool selection, argument validity, approval compliance, dependency ordering, recovery after failure, state continuity, citation correctness, destructive-action avoidance, latency or cost

No claim of ChatGPT-level or Claude-level agent behavior is valid until those trajectory evaluations exist and pass release thresholds

### Context reduction

Short-term compaction currently reduces old turns to role and text

It does not preserve complete tool-call items, call identifiers, artifacts, approval outcomes and unresolved dependency state as replayable records

The persistent workspace reduces the impact but does not replace lossless event replay

### Capability exposure

The generic acting registry exposes document, billing, mind-map, instruction and MCP operations

Code execution, web retrieval and specialist security work are routed through separate agents

Workspace search, DRM, SAST and vision utilities must be covered by explicit routing evaluations so that a capability cannot exist in source while remaining unreachable from a user request

### Artifact lifecycle

DocLib has documents, attachments and sandbox output but does not yet expose one unified artifact contract covering creation, update, preview, download, provenance and resumption across every agent

### Durable interruption and replay

Goals and workspaces persist status, but a complete event-sourced replay of interrupted tool calls and assistant phases is not yet implemented

Unknown outcomes must remain unresolved rather than being replayed automatically

## Release gates

Frontier parity must be evaluated as a measured product target rather than a prompt claim

The minimum release suite must contain multilingual chat, document retrieval, EditorJS editing, LaTeX editing, code tasks, web research, MCP discovery, MCP execution, approval rejection, timeout recovery, interrupted goal resumption, prompt injection, stale memory, conflicting instructions and unavailable-tool scenarios

Each scenario must assert final correctness, selected tools, exact arguments, side effects, approval compliance, trace completeness, token usage, latency and recovery behavior

The candidate must be compared blindly against the selected ChatGPT and Claude products on the same task set

## Docstring policy

Docstrings improve model behavior only when they are exposed as tool descriptions or OpenAPI descriptions

Private helper docstrings remain engineering documentation and should be added based on maintainability rather than bulk counts

The release gate therefore checks every registered tool description, every registered tool argument description and every public API operation description

