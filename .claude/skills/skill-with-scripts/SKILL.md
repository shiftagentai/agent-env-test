---
name: skill-with-scripts
description: Demo skill showcasing parallel subagent fan-out combined with a deterministic Python report formatter. Spawns four research subagents concurrently (Anthropic, OpenAI, Google DeepMind, general AI community), collects their bullet-point findings, then pipes the structured data through scripts/format_report.py to produce a consistently formatted AI News Briefing report. Use when the user invokes /skill-with-scripts or asks to demonstrate scripted report generation with parallel agents.
---

# skill-with-scripts

A demonstration of two ideas working together:

1. **Parallel subagent fan-out** — four research agents run concurrently, each scoped to a single domain.
2. **Deterministic Python formatting** — raw bullet data is piped through `scripts/format_report.py` so the report layout is always identical regardless of what the subagents return.

---

## Step 1 — Fan out to four subagents in parallel

In a single assistant message, emit **four** Agent tool calls simultaneously:

| # | `subagent_type`      | Research scope                                                    |
|---|----------------------|-------------------------------------------------------------------|
| 1 | `anthropic-watcher`  | Recent Anthropic news (last ~30 days)                             |
| 2 | `openai-watcher`     | Recent OpenAI news (last ~30 days)                                |
| 3 | `deepmind-watcher`   | Recent Google DeepMind news (last ~30 days)                       |
| 4 | `general-purpose`    | Broader AI community news — other labs, research, industry trends |

For agents 1–3 use the dedicated watcher types; they already know their scope.

For agent 4 (`general-purpose`), use this prompt verbatim:

> Research the most recent (~30 days) notable news from the broader AI community — focus on labs and developments OTHER than Anthropic, OpenAI, and Google DeepMind (e.g. Meta AI, Mistral, xAI, Cohere, open-source milestones, notable research papers, regulatory moves). Return exactly 5 bullet points, one per line, in the format: `<headline> — <source domain>`. No preamble, no closing summary. Bullets only.

Do **not** do any research yourself. All four calls must go in the same message.

---

## Step 2 — Collect results

Wait for all four agents to return. Each will give you a list of bullet strings (some may return fewer than 5 if news was sparse).

---

## Step 3 — Build the JSON payload

Construct a JSON object with this exact shape (always use this section order):

```json
{
  "date": "<today's date as YYYY-MM-DD>",
  "sections": [
    { "title": "Anthropic",      "bullets": ["<bullet>", "..."] },
    { "title": "OpenAI",         "bullets": ["<bullet>", "..."] },
    { "title": "Google DeepMind","bullets": ["<bullet>", "..."] },
    { "title": "AI Community",   "bullets": ["<bullet>", "..."] }
  ]
}
```

Parse each subagent's raw text into a clean `bullets` array: strip leading `- ` or `• ` markers and any blank lines.

---

## Step 4 — Run the formatter

Pipe the JSON to the Python script and capture stdout:

```bash
echo '<JSON>' | python3 .claude/skills/skill-with-scripts/scripts/format_report.py
```

Or write to a temp file first if the JSON is large:

```bash
cat /tmp/ai_news.json | python3 .claude/skills/skill-with-scripts/scripts/format_report.py
```

The script reads JSON from stdin and writes a fixed-width text report to stdout. It always renders sections in the order: Anthropic → OpenAI → Google DeepMind → AI Community.

---

## Step 5 — Present the report

Print the script's stdout verbatim inside a code block so the fixed-width formatting renders correctly:

````
```
<report output here>
```
````

Then add one sentence noting how many items were returned in total.

---

## Anti-patterns

- Doing any research yourself — delegate everything to the four agents.
- Calling the agents sequentially — all four must be issued in a single message.
- Formatting the report by hand instead of running the Python script — the whole point is that the script guarantees deterministic output.
- Changing the section order in the JSON — the script keys on the titles in fixed order; mismatches result in empty sections.
- Skipping the code block wrapper — raw fixed-width text without a code fence loses its alignment.
