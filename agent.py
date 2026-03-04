"""
Agent module — Core agent loop with Anthropic tool_use.
Week 2, Lonely Octopus AI Agent Bootcamp

Handles: system prompt construction, agentic tool loop, memory extraction.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from memory import MemoryManager
from tools import TOOL_DEFINITIONS, execute_tool

# Diverse advisor names — roughly 65% female, reflecting nonprofit sector demographics
ADVISOR_NAMES = [
    "Amara", "Priya", "Sofia", "Keiko", "Maya",
    "Luz", "Fatima", "Nia", "Elena", "Aisha",
    "Carmen", "Mei", "Tanya", "Aaliyah", "Rosa",
    "Gabriela", "Nkechi", "Suki", "Yara", "Ingrid",
    "Marcus", "David", "Ravi", "Carlos", "James",
    "Omar", "Andre", "Tomás", "Kwame", "Raj",
]

# Load API key
load_dotenv()
if not os.environ.get("ANTHROPIC_API_KEY"):
    load_dotenv(Path.home() / ".claude" / ".env")

MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic()
memory = MemoryManager()


def _pick_advisor_name(org_name: str) -> str:
    """Deterministically pick an advisor name based on org name (consistent across sessions)."""
    idx = int(hashlib.md5(org_name.encode()).hexdigest(), 16) % len(ADVISOR_NAMES)
    return ADVISOR_NAMES[idx]


def build_system_prompt(org_profile: dict) -> str:
    """Build the system prompt with org context and memory."""
    org_name = org_profile.get("org_name", "Unknown Organization")
    advisor_name = _pick_advisor_name(org_name)

    # Base prompt
    prompt = f"""# Role
You are an AI-powered nonprofit technology advisor created by Meet the Moment (MTM),
a consultancy that helps nonprofits harness technology to amplify their impact.
Your name is {advisor_name} — a friendly first name to make the conversation feel personal.

IMPORTANT: You are an AI advisor, not a human. Be transparent about this. On first greeting,
introduce yourself naturally, e.g., "Hi, I'm {advisor_name}, your AI technology advisor from
Meet the Moment." Do NOT claim to be a real person, do NOT invent a last name, job title,
or personal backstory. You are an AI assistant trained on MTM's 30+ years of nonprofit
technology expertise, CISSP/CISM-level security knowledge, and experience with 1,000+
organizations.

# Task
Provide tailored technology guidance to nonprofit organizations based on their
specific profile, budget, capacity, and needs. Use your knowledge base tools to
ground advice in curated best practices, and use Wikipedia to explain technical
concepts when needed.

# Approach
- Always consider the organization's budget tier and IT capacity when recommending solutions
- Lead with practical, actionable advice — not theoretical frameworks
- Recommend nonprofit-specific pricing and programs (TechSoup, vendor nonprofit tiers)
- Flag security considerations proactively
- When discussing AI, reference the COMPAS framework (Context, Objective, Method, Performance, Assessment, Sharing)
- Use tools proactively — search the knowledge base for relevant guidance before giving advice
- Use Wikipedia to explain technical terms the user may not be familiar with

# Communication Style
- Warm, professional, and encouraging
- Use clear language — avoid jargon unless explaining it
- Structure responses with headers and bullet points for readability
- Be honest about tradeoffs and limitations
- When you don't know something, say so

# Constraints
- Never recommend solutions that exceed the organization's stated budget or capacity
- Always mention free/discounted nonprofit options before paid alternatives
- Flag when a recommendation requires technical expertise the org may not have
- Don't assume the organization has IT staff unless stated
- Never pretend to be human — always be transparent that you are an AI advisor
"""

    # Add org context
    prompt += f"\n# Current Organization Profile\n"
    for key, value in org_profile.items():
        if value:
            label = key.replace("_", " ").title()
            prompt += f"- **{label}**: {value}\n"

    # Add memory context if available
    memory_context = memory.format_memory_context(org_name)
    if memory_context:
        prompt += f"\n{memory_context}\n"
        prompt += (
            "\nYou have previous session history with this organization. "
            "Reference past discussions and decisions naturally when relevant. "
            "On the first message of a returning session, briefly acknowledge "
            "you remember them and what you've discussed before."
        )
    else:
        prompt += (
            "\nThis is your first session with this organization. Welcome them warmly "
            "and ask what technology challenges they're facing."
        )

    return prompt


def run_agent(
    messages: list[dict],
    org_profile: dict,
    on_tool_use: callable = None,
) -> tuple[str, list[dict]]:
    """
    Run the agentic tool-use loop.

    Args:
        messages: Conversation history (role/content dicts)
        org_profile: Current org profile from sidebar
        on_tool_use: Optional callback(tool_name, tool_input, tool_result) for transparency

    Returns:
        (response_text, tool_calls_log)
    """
    system = build_system_prompt(org_profile)
    tool_calls_log = []

    # Agentic loop — keeps going until the model stops calling tools
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Check if the model wants to use tools
        if response.stop_reason == "tool_use":
            # Process all tool calls in this response
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_result = execute_tool(tool_name, tool_input)

                    # Log for transparency
                    log_entry = {
                        "tool": tool_name,
                        "input": tool_input,
                        "result": tool_result,
                    }
                    tool_calls_log.append(log_entry)

                    if on_tool_use:
                        on_tool_use(tool_name, tool_input, tool_result)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result,
                    })

            # Append assistant response + tool results, then loop
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # Model returned a text response — we're done
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text

            return text, tool_calls_log


def extract_memory(org_name: str, user_message: str, assistant_response: str):
    """Extract topics, decisions, and preferences from the conversation turn."""
    try:
        extraction_response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=(
                "Extract structured information from this conversation turn between "
                "a nonprofit tech advisor and a client. Return JSON only, no other text."
            ),
            messages=[{
                "role": "user",
                "content": f"""User message: {user_message}

Assistant response: {assistant_response[:2000]}

Extract the following as JSON:
{{
  "topics": ["list of technology topics discussed"],
  "decisions": ["any decisions made or recommendations accepted"],
  "preferences": ["any stated preferences about tools, approaches, or priorities"]
}}

Only include items that are clearly stated. Return empty lists if nothing applies.""",
            }],
        )

        text = extraction_response.content[0].text.strip()
        # Handle markdown code blocks
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        extraction = json.loads(text)
        memory.update_from_extraction(org_name, extraction)
    except (json.JSONDecodeError, IndexError, KeyError, anthropic.APIError):
        pass  # Memory extraction is best-effort


# CLI test
if __name__ == "__main__":
    test_profile = {
        "org_name": "Hope Community Center",
        "budget_tier": "Under $5M",
        "staff_count": "30",
        "cause_area": "Community Services",
        "current_tech": "Gmail, spreadsheets, paper forms",
        "pain_points": "No donor tracking, manual processes",
        "it_capacity": "No dedicated IT staff",
    }

    memory.init_org("Hope Community Center", test_profile)

    messages = [{"role": "user", "content": "What CRM should we use for donor management?"}]
    print("Sending to agent...")
    response, tools = run_agent(messages, test_profile)
    print(f"\n{'='*60}")
    print(f"Tools used: {len(tools)}")
    for t in tools:
        print(f"  - {t['tool']}({json.dumps(t['input'])})")
    print(f"\n{'='*60}")
    print(response)
