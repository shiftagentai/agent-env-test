---
name: subagents-demo
description: Demonstrate parallel subagent fan-out by spawning three distinct research subagents concurrently — one each for Anthropic, OpenAI, and Google DeepMind recent news. Use when the user invokes /subagents-demo or asks to see/test the parallel subagent mechanic. The skill itself does no research; it issues three Agent tool calls in a single message so they execute in parallel, then collates their summaries.
---

# subagents-demo

A live demonstration that one skill invocation can fan out to multiple subagents running concurrently. When this skill is invoked, you MUST spawn **all three** of the following subagent types **in a single message** so they run in parallel:

- `anthropic-watcher` — research recent Anthropic news
- `openai-watcher` — research recent OpenAI news
- `deepmind-watcher` — research recent Google DeepMind news

## How to run

1. In one assistant turn, emit a single message containing **three** Agent tool calls — one targeting each subagent type. Do not call them sequentially. Do not await one before issuing the next. All three calls go in the same message.

2. For each Agent call, pass:
   - `subagent_type`: the agent name (`anthropic-watcher`, `openai-watcher`, or `deepmind-watcher`)
   - `description`: a 3–5 word label (e.g. "Anthropic recent news")
   - `prompt`: a short, self-contained instruction — the subagent has no context from this conversation. Tell it to research the most recent (last ~30 days) public news for its lab and return ~5 bullet points. Mention that the result is being collated into a side-by-side comparison so it should not pad with preamble.

3. When all three results return, present them as three labeled sections in the order Anthropic → OpenAI → DeepMind. Do not editorialize or merge; render each subagent's bullets verbatim under its lab heading.

## What to say to the user before fanning out

One sentence stating you're spawning three subagents in parallel. Then issue the three Agent calls.

## What to say after

One sentence noting all three returned, then the three labeled sections.

## Anti-patterns

- Doing the research yourself with WebSearch — that defeats the demo. The whole point is to delegate.
- Spawning the subagents one at a time across multiple messages — that's sequential, not parallel.
- Spawning a generic `Explore` or `general-purpose` agent instead of the three named types — those exist in this environment, but the demo specifically exercises the three custom subagents defined alongside this skill.
- Adding a fourth synthesizer subagent — keep it to exactly three.
