"""
Memory module — JSON-backed persistent memory per organization.
Week 2, Lonely Octopus AI Agent Bootcamp

Stores org profiles, key decisions, topics discussed, and preferences.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

MEMORY_DIR = Path(__file__).parent / "data"
MEMORY_FILE = MEMORY_DIR / "memory.json"


class MemoryManager:
    """Manages persistent memory for organizations across sessions."""

    def __init__(self):
        MEMORY_DIR.mkdir(exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        """Load memory from disk."""
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        """Persist memory to disk."""
        with open(MEMORY_FILE, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def get_org(self, org_name: str) -> Optional[dict]:
        """Get stored memory for an organization."""
        return self.data.get(org_name)

    def has_org(self, org_name: str) -> bool:
        """Check if we have memory for this org."""
        return org_name in self.data

    def init_org(self, org_name: str, profile: dict):
        """Initialize or update an org's profile."""
        if org_name not in self.data:
            self.data[org_name] = {
                "profile": profile,
                "first_session": datetime.now().isoformat(),
                "session_count": 0,
                "topics_discussed": [],
                "key_decisions": [],
                "preferences": [],
            }
        else:
            self.data[org_name]["profile"] = profile

        self.data[org_name]["session_count"] = self.data[org_name].get("session_count", 0) + 1
        self.data[org_name]["last_session"] = datetime.now().isoformat()
        self._save()

    def add_topic(self, org_name: str, topic: str):
        """Record a topic that was discussed."""
        if org_name in self.data:
            topics = self.data[org_name].setdefault("topics_discussed", [])
            if topic not in topics:
                topics.append(topic)
                self._save()

    def add_decision(self, org_name: str, decision: str):
        """Record a key decision or recommendation."""
        if org_name in self.data:
            decisions = self.data[org_name].setdefault("key_decisions", [])
            entry = {"decision": decision, "date": datetime.now().isoformat()}
            decisions.append(entry)
            self._save()

    def add_preference(self, org_name: str, preference: str):
        """Record an organizational preference."""
        if org_name in self.data:
            prefs = self.data[org_name].setdefault("preferences", [])
            if preference not in prefs:
                prefs.append(preference)
                self._save()

    def format_memory_context(self, org_name: str) -> str:
        """Format stored memory as context for the system prompt."""
        org = self.get_org(org_name)
        if not org:
            return ""

        parts = [f"## Memory from Previous Sessions (Session #{org['session_count']})"]
        parts.append(f"First session: {org.get('first_session', 'unknown')}")
        parts.append(f"Last session: {org.get('last_session', 'unknown')}")

        if org.get("topics_discussed"):
            parts.append(f"\n### Topics Previously Discussed")
            for t in org["topics_discussed"][-10:]:  # Last 10
                parts.append(f"- {t}")

        if org.get("key_decisions"):
            parts.append(f"\n### Key Decisions Made")
            for d in org["key_decisions"][-10:]:  # Last 10
                parts.append(f"- {d['decision']} ({d['date'][:10]})")

        if org.get("preferences"):
            parts.append(f"\n### Known Preferences")
            for p in org["preferences"]:
                parts.append(f"- {p}")

        return "\n".join(parts)

    def update_from_extraction(self, org_name: str, extraction: dict):
        """Update memory from an AI extraction result."""
        if org_name not in self.data:
            return

        for topic in extraction.get("topics", []):
            self.add_topic(org_name, topic)

        for decision in extraction.get("decisions", []):
            self.add_decision(org_name, decision)

        for pref in extraction.get("preferences", []):
            self.add_preference(org_name, pref)


# CLI test
if __name__ == "__main__":
    mm = MemoryManager()

    # Simulate a session
    mm.init_org("Test Nonprofit", {
        "org_name": "Test Nonprofit",
        "budget_tier": "Under $5M",
        "staff_count": "25",
        "cause_area": "Education",
    })
    mm.add_topic("Test Nonprofit", "CRM selection")
    mm.add_decision("Test Nonprofit", "Will evaluate Bloomerang for donor management")
    mm.add_preference("Test Nonprofit", "Prefers cloud-based solutions")

    print("=== Memory Context ===")
    print(mm.format_memory_context("Test Nonprofit"))
    print()
    print(f"Memory file: {MEMORY_FILE}")
    print(f"Org exists: {mm.has_org('Test Nonprofit')}")
