---
name: custom-test-customer-skill
description: Greet the user and fetch the latest Anthropic news. Use this skill whenever the user asks for a friendly hello combined with recent Anthropic updates, wants to know what's new at Anthropic, or asks for an Anthropic news briefing. Also trigger when the user says "custom test customer skill" or asks for a greeting with news.
---

# Custom Test Customer Skill

When this skill is invoked:

## 1. Greet the user

Start with a warm, friendly hello message. Keep it brief and natural — something like "Hello! Welcome — glad you're here." Adapt the tone to feel conversational rather than robotic.

## 2. Look up the latest Anthropic news

Use the WebSearch tool to search for recent Anthropic news. Good search queries to try:

- "Anthropic news latest"
- "Anthropic Claude announcements"

Focus on results from the last 30 days. If WebSearch is not available, let the user know and skip this step gracefully.

## 3. Present the findings

Summarize what you found in a short, scannable format:

- Use 3-5 bullet points covering the most notable items (product launches, model releases, partnerships, research papers, company announcements).
- Include the date or timeframe for each item when available.
- Keep each bullet to 1-2 sentences.
- If a source URL is available, mention it so the user can read more.

End with a brief closing line inviting the user to ask follow-up questions about any of the news items.
