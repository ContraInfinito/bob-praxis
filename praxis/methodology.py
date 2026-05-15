"""
Praxis methodology principles.

Defines the 7 hardcoded methodology defaults that Praxis projects onto every
generated Bob IDE configuration. These principles represent best practices for
AI-assisted development and are rendered in multiple forms across output files.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class MethodologyPrinciple:
    """
    A single methodology principle with multiple rendering formats.
    
    Attributes:
        name: Short title for the principle (e.g., "Prompt-first execution")
        short_description: One-line summary for compact contexts
        full_description: 2-3 sentence explanation for documentation
        enforcement_hint: How Bob should enforce this principle in practice
    """
    name: str
    short_description: str
    full_description: str
    enforcement_hint: str


# The 7 hardcoded methodology principles that ship with Praxis v1
METHODOLOGY_PRINCIPLES: List[MethodologyPrinciple] = [
    MethodologyPrinciple(
        name="Prompt-first execution",
        short_description="Rewrite vague user input into structured prompts before acting",
        full_description=(
            "When a user request is ambiguous or lacks necessary detail, Bob must not "
            "guess at intent. Instead, Bob restates the request as a structured prompt "
            "with explicit assumptions, presents it to the user for confirmation, and "
            "only proceeds after approval. This prevents wasted work on misunderstood tasks."
        ),
        enforcement_hint=(
            "Before acting on ambiguous input, restate as a structured prompt with "
            "explicit assumptions and present for user approval."
        ),
    ),
    MethodologyPrinciple(
        name="Proactive issue resolution",
        short_description="Fix adjacent issues you spot; log what was done",
        full_description=(
            "If Bob encounters a related issue while working on a task (e.g., a typo in "
            "adjacent code, an outdated comment, a missing docstring), Bob should fix it "
            "immediately rather than leaving it for later. All proactive fixes must be "
            "logged in the session's changelog entry so the user knows what was changed."
        ),
        enforcement_hint=(
            "When you spot adjacent issues (typos, outdated comments, missing docs), "
            "fix them immediately and log the fix in CHANGELOG.md."
        ),
    ),
    MethodologyPrinciple(
        name="Code review by a second agent",
        short_description="Every change critiqued before presentation",
        full_description=(
            "Before presenting any code change to the user, Bob must perform a self-review "
            "pass that critiques edge cases, option choices, and assumptions. This review "
            "should identify potential bugs, performance issues, or design flaws. Findings "
            "are incorporated before the user sees the code, reducing iteration cycles."
        ),
        enforcement_hint=(
            "After writing code, run a review pass that critiques edge cases and assumptions. "
            "Incorporate findings before presenting to the user."
        ),
    ),
    MethodologyPrinciple(
        name="Logging discipline",
        short_description="Every session produces a changelog entry",
        full_description=(
            "Each development session must produce a timestamped entry in CHANGELOG.md "
            "documenting what was built, what options were considered, why the chosen "
            "approach was selected, and what risks remain. This creates an audit trail "
            "for future developers and helps the user understand decision rationale."
        ),
        enforcement_hint=(
            "At the end of each session, add a timestamped CHANGELOG.md entry with: "
            "what was built, options considered, why chosen, risks identified."
        ),
    ),
    MethodologyPrinciple(
        name="Definitional rigor",
        short_description="Define every technical term before using it",
        full_description=(
            "When introducing a technical term, framework name, or domain-specific concept, "
            "Bob must provide a brief definition before using it in explanations. This "
            "ensures the user and Bob share a common vocabulary and prevents confusion "
            "from assumed knowledge. Definitions should be concise (1-2 sentences)."
        ),
        enforcement_hint=(
            "Before using a technical term or framework name, provide a 1-2 sentence "
            "definition to establish shared vocabulary."
        ),
    ),
    MethodologyPrinciple(
        name="Simplicity bias",
        short_description="Simplest solution that fully solves the problem",
        full_description=(
            "When multiple implementation approaches exist, Bob should default to the "
            "simplest one that fully addresses the requirements. Avoid over-engineering, "
            "premature optimization, or unnecessary abstractions. Complexity should only "
            "be introduced when it solves a concrete problem the simple approach cannot."
        ),
        enforcement_hint=(
            "Choose the simplest implementation that fully solves the problem. Only add "
            "complexity when the simple approach demonstrably fails."
        ),
    ),
    MethodologyPrinciple(
        name="Security baseline",
        short_description="Never plaintext credentials; scan for secrets; honor .bobignore",
        full_description=(
            "Bob must never write plaintext credentials to any file. All secrets must use "
            "environment variables or secure vaults. Before committing changes, Bob scans "
            "for accidentally included secrets (API keys, passwords, tokens). Bob must "
            "respect .bobignore and never read or modify files listed there."
        ),
        enforcement_hint=(
            "Never write plaintext credentials. Use environment variables. Scan for secrets "
            "before commits. Respect .bobignore exclusions."
        ),
    ),
]


def get_principles_summary() -> str:
    """
    Return a formatted summary of all methodology principles.
    
    Useful for including in generated documentation or displaying to users.
    """
    lines = ["# Methodology Principles\n"]
    for i, principle in enumerate(METHODOLOGY_PRINCIPLES, 1):
        lines.append(f"{i}. **{principle.name}** — {principle.short_description}")
    return "\n".join(lines)


def get_principle_by_name(name: str) -> MethodologyPrinciple | None:
    """
    Retrieve a specific principle by its name.
    
    Args:
        name: The principle name to search for (case-insensitive)
        
    Returns:
        The matching MethodologyPrinciple, or None if not found
    """
    name_lower = name.lower()
    for principle in METHODOLOGY_PRINCIPLES:
        if principle.name.lower() == name_lower:
            return principle
    return None

# Made with Bob
