"""
Tools module — Knowledge base search + Wikipedia lookup.
Week 2, Lonely Octopus AI Agent Bootcamp

Provides tool definitions for Anthropic tool_use and execution functions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

import requests

# Load knowledge base once at import
KB_PATH = Path(__file__).parent / "knowledge_base.json"
with open(KB_PATH) as f:
    KNOWLEDGE_BASE = json.load(f)

# --- Tool definitions for Anthropic API ---

TOOL_DEFINITIONS = [
    {
        "name": "search_knowledge_base",
        "description": (
            "Search MTM's curated nonprofit technology knowledge base for guidance on "
            "topics like CRM selection, cybersecurity, Microsoft 365, AI adoption, "
            "cloud migration, budgeting, and more. Use this when the user asks about "
            "specific technology decisions, tools, or best practices for nonprofits."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query — topic, tool name, or question keywords",
                },
                "budget_tier": {
                    "type": "string",
                    "enum": ["small", "large", "all"],
                    "description": "Filter by budget tier: 'small' (under $5M), 'large' ($5M+), or 'all'",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_wikipedia_summary",
        "description": (
            "Fetch a plain-language summary of a concept from Wikipedia. Use this when "
            "the user asks 'What is X?' for a general technology concept, standard, "
            "framework, or term that isn't specific to nonprofit technology guidance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to look up (e.g., 'NIST', 'MFA', 'ransomware')",
                },
            },
            "required": ["topic"],
        },
    },
]


def search_knowledge_base(query: str, budget_tier: str = "all") -> List[dict]:
    """Search the knowledge base by keyword matching and optional budget filter."""
    query_lower = query.lower()
    query_words = set(re.split(r"\W+", query_lower)) - {"", "a", "the", "for", "and", "or", "is", "in", "to", "of"}

    scored = []
    for entry in KNOWLEDGE_BASE:
        # Budget tier filter
        if budget_tier != "all" and entry["budget_tier"] not in (budget_tier, "all"):
            continue

        # Score based on keyword matches
        score = 0
        searchable = f"{entry['title']} {' '.join(entry['keywords'])} {entry['category']}".lower()

        for word in query_words:
            if word in searchable:
                score += 2
            # Partial match in content
            if word in entry["content"].lower():
                score += 1

        # Exact keyword matches get a boost
        for kw in entry["keywords"]:
            if kw in query_lower:
                score += 3

        if score > 0:
            scored.append((score, entry))

    # Sort by score descending, return top 3
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [
        {"title": e["title"], "content": e["content"], "category": e["category"]}
        for _, e in scored[:3]
    ]

    if not results:
        return [{"title": "No results", "content": f"No knowledge base entries matched '{query}'. Try broader terms or ask me directly — I may still be able to help.", "category": "none"}]

    return results


def fetch_wikipedia_summary(topic: str) -> str:
    """Fetch a summary from the Wikipedia REST API."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(topic)}"
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "MTM-Advisor/1.0"})
        if resp.status_code == 200:
            data = resp.json()
            return f"**{data.get('title', topic)}**: {data.get('extract', 'No summary available.')}"
        elif resp.status_code == 404:
            # Try search API as fallback
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={requests.utils.quote(topic)}&format=json&srlimit=1"
            search_resp = requests.get(search_url, timeout=10, headers={"User-Agent": "MTM-Advisor/1.0"})
            if search_resp.status_code == 200:
                results = search_resp.json().get("query", {}).get("search", [])
                if results:
                    # Retry with the first search result title
                    title = results[0]["title"]
                    retry_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
                    retry_resp = requests.get(retry_url, timeout=10, headers={"User-Agent": "MTM-Advisor/1.0"})
                    if retry_resp.status_code == 200:
                        data = retry_resp.json()
                        return f"**{data.get('title', topic)}**: {data.get('extract', 'No summary available.')}"
            return f"Could not find a Wikipedia article for '{topic}'."
        else:
            return f"Wikipedia API returned status {resp.status_code} for '{topic}'."
    except requests.RequestException as e:
        return f"Error fetching Wikipedia summary: {e}"


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return the result as a string."""
    if tool_name == "search_knowledge_base":
        results = search_knowledge_base(
            query=tool_input["query"],
            budget_tier=tool_input.get("budget_tier", "all"),
        )
        return json.dumps(results, indent=2)
    elif tool_name == "fetch_wikipedia_summary":
        return fetch_wikipedia_summary(topic=tool_input["topic"])
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


# CLI test
if __name__ == "__main__":
    print("=== Knowledge Base Search: 'CRM' ===")
    results = search_knowledge_base("CRM", "small")
    for r in results:
        print(f"  [{r['category']}] {r['title']}")
    print()

    print("=== Knowledge Base Search: 'security MFA' ===")
    results = search_knowledge_base("security MFA")
    for r in results:
        print(f"  [{r['category']}] {r['title']}")
    print()

    print("=== Wikipedia: 'NIST' ===")
    print(fetch_wikipedia_summary("NIST"))
    print()

    print("=== Wikipedia: 'Multi-factor authentication' ===")
    print(fetch_wikipedia_summary("Multi-factor authentication"))
