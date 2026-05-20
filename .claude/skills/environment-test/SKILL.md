---
name: environment-test
description: A basic diagnostic skill that checks and reports the AI model name and version powering the current agent session, along with other environment details. Use this skill whenever the user wants to know what model is running, check the agent environment, run a diagnostic, or verify the AI version. Also trigger when the user asks "what model are you?", "which Claude version?", "agent diagnostics", or similar environment/version queries.
---

# Environment Test Skill

You are running an environment diagnostic. When invoked:

1. **AI Model**: Print the AI model name and version you are running as (e.g., "Claude Opus 4.6", "Claude Sonnet 4.6"). Use the model identity from your system prompt — look for phrases like "You are powered by" or the model ID. Print both the human-readable name and the exact model ID if available.

2. **Date and Time**: Print the current date and time (use the Bash tool: `date`).

3. **Working Directory**: Print the current working directory (use the Bash tool: `pwd`).

4. **Platform Info**: Print the OS and platform info (use the Bash tool: `uname -a`).

5. Print "Environment diagnostic complete."

Keep your response brief and structured. Use a clear heading for each section.
