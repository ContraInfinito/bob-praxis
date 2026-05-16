"""
Praxis inference prompts.

Builds the natural-language prompts that the host agent (Bob) answers during
Phase 1 of the two-phase handshake. Output of each builder is a dict with:

- prompt_for_bob: the natural-language instruction for the host agent
- partial_context: deterministic fields already known (no inference needed)
- meta: schema version, mode, source path

Phase 2 (cli.py::generate_command) consumes the partial_context plus the host
agent's JSON answer (bob_inference) and renders the Praxis output files.
"""

from pathlib import Path

from praxis.detect import StackInfo
from praxis.generate import _read_project_readme


__all__ = ["build_analyze_prompt", "build_plan_prompt"]


# Shared tone constraint, lifted verbatim from the legacy Granite prompts so
# the new Bob-mediated path produces prose with the same voice.
_TONE_RULES = (
    "Tone rules: plain, direct prose. No corporate language. Do not use phrases "
    "like 'embark on', 'forge a partnership', 'shape the future', 'exceed "
    "expectations', 'ambitious endeavor', 'cutting-edge', 'leveraging', "
    "'pioneering'. Sound like a competent engineer briefing a coworker, not a "
    "CEO opening a keynote."
)


def _frameworks_for_prompt(frameworks: list[str]) -> str:
    """Format frameworks list for embedding in the prompt to the host agent."""
    if not frameworks:
        return "none detected"
    return ", ".join(frameworks)


def _dependencies_for_prompt(dependencies: list[str]) -> str:
    """
    Format dependencies for the prompt. Unlike the template-display formatter,
    no truncation here — the host agent benefits from seeing the full list.
    """
    if not dependencies:
        return "none detected"
    return ", ".join(dependencies)


def build_analyze_prompt(stack_info: StackInfo, project_path: Path) -> dict:
    """
    Build the Phase 1 prompt for analyze mode.

    Reads deterministic project facts (stack, dependencies, README excerpt) and
    composes a natural-language prompt the host agent answers with a JSON
    object containing intro_prose, skill_content, and agents_context.

    Args:
        stack_info: Result of praxis.detect.detect_stack()
        project_path: Path to the project directory being analyzed

    Returns:
        Dict with keys: prompt_for_bob, partial_context, meta
    """
    project_name = project_path.name
    frameworks_str = _frameworks_for_prompt(stack_info.frameworks)
    dependencies_str = _dependencies_for_prompt(stack_info.dependencies)
    readme_excerpt = _read_project_readme(project_path)

    # Grounding block: README excerpt if present, conservative fallback if not
    if readme_excerpt:
        grounding_block = (
            f"\n\nProject README excerpt (use this as ground truth about what the "
            f"project actually does — do not invent a different purpose):\n"
            f"---\n{readme_excerpt}\n---"
        )
    else:
        grounding_block = (
            f"\n\nNo README available. Describe the project conservatively based "
            f"only on its name, stack, and frameworks. Do not invent."
        )

    prompt_for_bob = (
        f"You are helping bootstrap Bob IDE configuration for an existing codebase "
        f"via the Praxis methodology-transfer tool. Read the project context below "
        f"and return a JSON object with three string fields.\n\n"
        f"PROJECT CONTEXT:\n"
        f"- Project name: {project_name}\n"
        f"- Stack: {stack_info.stack_name}\n"
        f"- Detected frameworks: {frameworks_str}\n"
        f"- Detected dependencies: {dependencies_str}\n"
        f"- Python files count: {stack_info.python_files_count}"
        f"{grounding_block}\n\n"
        f"REQUIRED OUTPUT — return EXACTLY this JSON shape (no preamble, no code "
        f"fences, no commentary, no multiple versions):\n"
        f"{{\n"
        f'  "intro_prose": "<2 short paragraphs, 4-5 sentences total, addressing '
        f"Bob in second person about working on this project; mention the detected "
        f"frameworks or dependencies concretely; focus on day-to-day collaboration, "
        f"not abstract goals; no 'Dear Bob' salutation, no signature>\",\n"
        f'  "skill_content": "<5-8 bullet points (each starting with - ) covering '
        f"Python-specific conventions relevant to this dependency set; if pytest "
        f"is present, include a bullet on test conventions; if Flask or FastAPI is "
        f"present, include a bullet on web framework patterns; if pandas/numpy is "
        f"present, include a bullet on data handling; no preamble, no header, no "
        f'closing>",\n'
        f'  "agents_context": "<2-3 factual sentences describing what this project '
        f"does, written for an AI development partner to read at session start; if "
        f"you don't know what the project does, say so plainly instead of inventing "
        f'a purpose>"\n'
        f"}}\n\n"
        f"{_TONE_RULES}\n\n"
        f"Return EXACTLY ONE JSON object. Start with {{ and end with }}."
    )

    partial_context = {
        "project_name": project_name,
        "stack_name": stack_info.stack_name,
        "frameworks": list(stack_info.frameworks),
        "dependencies": list(stack_info.dependencies),
        "python_files_count": stack_info.python_files_count,
        "grounding_context": readme_excerpt,
        "grounding_source_label": "README",
        "mode": "analyze",
    }

    meta = {
        "schema_version": "1.0",
        "mode": "analyze",
        "path": str(project_path),
    }

    return {
        "prompt_for_bob": prompt_for_bob,
        "partial_context": partial_context,
        "meta": meta,
    }


def build_plan_prompt(doc_path: Path, doc_content: str) -> dict:
    """
    Build the Phase 1 prompt for plan mode.

    Unlike analyze mode (which calls detect_stack first), plan mode delegates
    BOTH the stack/framework inference and the prose generation to the host
    agent in a single response. This collapses what was previously two Granite
    calls (one for JSON extraction in plan.py, three for prose in generate.py)
    into one prompt.

    Args:
        doc_path: Path to the planning document (.md / .markdown / .txt)
        doc_content: Already-read document content (caller handles encoding)

    Returns:
        Dict with keys: prompt_for_bob, partial_context, meta
    """
    project_name = doc_path.stem

    # Cap document content for the prompt — long docs waste host-agent context
    if len(doc_content) > 8000:
        doc_for_prompt = doc_content[:8000] + "\n\n...[document truncated]"
    else:
        doc_for_prompt = doc_content

    # Separate, smaller excerpt for the partial_context. The downstream
    # GenerationContext only needs ~1500 chars of grounding for the templates.
    doc_excerpt = doc_content[:1500]

    prompt_for_bob = (
        f"You are helping bootstrap Bob IDE configuration from a planning document "
        f"via the Praxis methodology-transfer tool. Read the planning document "
        f"below and return a JSON object describing the planned project AND "
        f"providing the prose content for Praxis's output files. The project "
        f"doesn't yet exist — the document is the only source of truth.\n\n"
        f"PROJECT METADATA:\n"
        f"- Project name (from document filename): {project_name}\n\n"
        f"PLANNING DOCUMENT:\n"
        f"---\n{doc_for_prompt}\n---\n\n"
        f"REQUIRED OUTPUT — return EXACTLY this JSON shape (no preamble, no code "
        f"fences, no commentary, no multiple versions):\n"
        f"{{\n"
        f'  "inferred_stack": "Python" | "Generic",\n'
        f'  "inferred_frameworks": [<subset of: "Flask", "FastAPI", "Django", '
        f'"pandas", "numpy", "pytest"; empty list if none apply; do not invent>],\n'
        f'  "project_purpose": "<1-2 sentence factual description of what the '
        f"project will do; if the document is too vague, say so plainly instead of "
        f'inventing a purpose>",\n'
        f'  "features": [<3-7 short phrases, each 3-8 words, concrete features '
        f"not abstract goals>],\n"
        f'  "integrations": [<external systems explicitly mentioned: databases, '
        f"APIs, third-party services; empty list if none>],\n"
        f'  "clarifying_questions": [<0-5 questions about gaps in the document a '
        f"developer would need to know; be honest, most planning docs have gaps>],\n"
        f'  "intro_prose": "<2 short paragraphs, 4-5 sentences total, addressing '
        f"Bob in second person about working on this future project; mention the "
        f"inferred frameworks concretely; focus on day-to-day collaboration>\",\n"
        f'  "skill_content": "<5-8 bullet points (each starting with - ) covering '
        f"Python-specific conventions relevant to the inferred frameworks; if "
        f"pytest is inferred, include a bullet on test conventions; if Flask or "
        f"FastAPI is inferred, include a bullet on web framework patterns>\",\n"
        f'  "agents_context": "<2-3 factual sentences describing what this project '
        f"will do, written for an AI development partner; note the project is in "
        f'planning phase>"\n'
        f"}}\n\n"
        f"Rules for the inference fields:\n"
        f"- inferred_stack: 'Python' if the document mentions Python, Flask, "
        f"FastAPI, Django, pandas, numpy, pytest, or any Python-specific concept. "
        f"Otherwise 'Generic'.\n"
        f"- inferred_frameworks: ONLY from the allowed set above. Do not invent "
        f"framework names.\n"
        f"- features: each 3-8 words, concrete, not abstract goals.\n"
        f"- clarifying_questions: about things the document did NOT specify but a "
        f"developer would need to know. Empty list ONLY if the document is fully "
        f"specified — be honest, most aren't.\n\n"
        f"{_TONE_RULES}\n\n"
        f"Return EXACTLY ONE JSON object. Start with {{ and end with }}."
    )

    partial_context = {
        "project_name": project_name,
        # stack_name, frameworks, features, integrations, clarifying_questions,
        # and project_purpose all come from bob_inference, not partial_context.
        "grounding_context": doc_excerpt,
        "grounding_source_label": "planning document",
        "mode": "plan",
    }

    meta = {
        "schema_version": "1.0",
        "mode": "plan",
        "path": str(doc_path),
    }

    return {
        "prompt_for_bob": prompt_for_bob,
        "partial_context": partial_context,
        "meta": meta,
    }
