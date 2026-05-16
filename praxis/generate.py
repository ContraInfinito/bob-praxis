"""
Praxis generation engine.

Assembles templates with detected stack information and host-agent-provided
prose content to produce tailored configuration files for one of three
supported targets:

  - bob          → <root>/praxis_output/ (six files)
  - claude-code  → <root>/CLAUDE.md
  - cursor       → <root>/.cursor/rules/{methodology,python}.mdc

Phase 4-revised: this module is a pure templating engine. The host agent (Bob,
or any compatible orchestrator) supplies the inference output via the
GenerationContext; this module does no LLM calls of its own.

Sub-task 4.2: multi-target dispatch. The same GenerationContext can be
rendered against any of the three target template families. Templates live in
``praxis/templates/<target>/`` and each target has its own idiomatic output
location.
"""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone

from praxis.detect import StackInfo
from praxis.methodology import METHODOLOGY_PRINCIPLES


__all__ = [
    "generate_outputs",
    "_stack_info_to_context",
    "_read_project_readme",
    "_sanitize_inference_output",
    "GenerationContext",
    "ALLOWED_TARGETS",
]


# Targets the engine knows how to render for. Sub-tasks 4.3 / 4.4 fill in the
# claude-code and cursor template content; this sub-task wires the dispatch.
ALLOWED_TARGETS = ("bob", "claude-code", "cursor")


@dataclass
class GenerationContext:
    """
    Unified input for the generation engine.

    Built from StackInfo (analyze mode) or directly from the Phase 2 JSON
    blob (plan mode). The three inference fields (intro_prose, skill_content,
    agents_context) are filled by the host agent via Phase 1's bob_inference
    output, never by code inside this module.
    """
    project_name: str
    stack_name: str  # "Python" or "Generic"
    frameworks: list[str] = field(default_factory=list)

    # Analyze-mode fields (empty for plan mode)
    dependencies: list[str] = field(default_factory=list)
    python_files_count: int = 0

    # Plan-mode fields (empty for analyze mode)
    project_purpose: str = ""
    features: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    clarifying_questions: list[str] = field(default_factory=list)

    # Grounding context (README for analyze, source doc excerpt for plan)
    grounding_context: str = ""
    grounding_source_label: str = ""  # "README" or "planning document"

    # Mode flag for template branching
    mode: str = "analyze"  # "analyze" or "plan"

    # Host-agent-provided inference fields (filled by generate_command in cli.py
    # from the bob_inference JSON sub-object). Empty defaults let templates
    # render with placeholders if a caller skips Phase 1.
    intro_prose: str = ""
    skill_content: str = ""
    agents_context: str = ""

    # Output target: which configuration family to render. Phase 1 stamps this
    # into partial_context/meta so Phase 2 honors what Phase 1 was told.
    target: str = "bob"  # "bob" | "claude-code" | "cursor"


def _sanitize_inference_output(text: str) -> str:
    """
    Strip common host-agent output artifacts before insertion into templates.

    Removes instruction-echo preambles ("Remember to...", "Output only...",
    "Sure,...", etc.), wrapping code fences, outer wrapping quotes, and orphan
    trailing quotes. Originally written for IBM Granite's failure modes; kept
    as a defensive safety net for Bob's output too. May be removed in a later
    sub-task if Bob's output is reliably clean.
    """
    text = text.strip()

    # Strip wrapping code fences (the host agent sometimes wraps prose in ```...```)
    if text.startswith("```"):
        # Skip the opening fence line (which may have a language tag like ```python)
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        else:
            text = text[3:]
        # Strip closing fence
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].rstrip()
    text = text.strip()

    # Strip leading instruction-echo lines
    instruction_echoes = (
        "Remember to", "Output only", "Output ONLY", "Output will", "Output:",
        "Write a", "Write 2", "Write the", "Use double", "Use single", "Use the",
        "Here is", "Here's", "Sure,", "Certainly,", "Below is", "As requested",
        "Of course", "Note:", "Notes:", "Response:", "Answer:", "Following the",
        "Per the", "Per your", "As per", "Based on",
    )
    lines = text.split("\n")
    while lines and any(lines[0].strip().startswith(p) for p in instruction_echoes):
        lines = lines[1:]
    text = "\n".join(lines).strip()

    # Strip outer wrapping quotes if the host agent wrapped the entire output
    # in matched double quotes. Safety check: don't strip if removing the outer
    # pair would expose another quote, which would mean we're mangling
    # legitimate nested quotation marks.
    if (
        len(text) >= 2
        and text.startswith('"')
        and text.endswith('"')
        and text.count('"') >= 2
        and text.count('"') % 2 == 0
    ):
        inner = text[1:-1].strip()
        if not (inner.startswith('"') or inner.endswith('"')):
            text = inner

    # Strip orphan trailing quote (closing quote without matching opening)
    if text.endswith('"') and text.count('"') % 2 == 1:
        text = text[:-1].rstrip()

    return text


def _format_frameworks_list(frameworks: list[str]) -> str:
    """Format frameworks list for display in templates."""
    if not frameworks:
        return "none detected"
    return ", ".join(frameworks)


def _format_dependencies_list(dependencies: list[str]) -> str:
    """Format dependencies list for display, truncating if too long."""
    if not dependencies:
        return "none detected"

    if len(dependencies) <= 10:
        return ", ".join(dependencies)

    # Truncate to first 10 and add count
    truncated = ", ".join(dependencies[:10])
    remaining = len(dependencies) - 10
    return f"{truncated}...and {remaining} more"


def _render_methodology_short() -> str:
    """Render methodology principles in short form (bulleted list)."""
    lines = []
    for i, principle in enumerate(METHODOLOGY_PRINCIPLES, 1):
        lines.append(f"{i}. **{principle.name}** — {principle.short_description}")
    return "\n".join(lines)


def _render_methodology_full() -> str:
    """Render methodology principles in full form (headers + paragraphs)."""
    lines = []
    for i, principle in enumerate(METHODOLOGY_PRINCIPLES, 1):
        lines.append(f"#### {i}. {principle.name}")
        lines.append("")
        lines.append(principle.full_description)
        lines.append("")
    return "\n".join(lines)


def _render_methodology_enforcement() -> str:
    """Render methodology principles in enforcement form (bulleted list)."""
    lines = []
    for i, principle in enumerate(METHODOLOGY_PRINCIPLES, 1):
        lines.append(f"{i}. **{principle.name}**: {principle.enforcement_hint}")
    return "\n".join(lines)


def _generate_framework_notes(frameworks: list[str]) -> str:
    """Generate framework-specific notes for python_skill.md."""
    if not frameworks:
        return "No frameworks detected. This appears to be a general-purpose Python project."

    notes = []

    if "Flask" in frameworks:
        notes.append("""
### Flask

- Use blueprints for modular route organization
- Store configuration in environment variables, not hardcoded
- Use Flask's `current_app` for accessing app context
- Test routes using Flask's test client
""")

    if "FastAPI" in frameworks:
        notes.append("""
### FastAPI

- Use Pydantic models for request/response validation
- Leverage dependency injection for shared logic
- Use async/await for I/O-bound operations
- Document endpoints with docstrings (auto-generates OpenAPI docs)
""")

    if "Django" in frameworks:
        notes.append("""
### Django

- Follow Django's MVT (Model-View-Template) pattern
- Use Django ORM for database operations
- Leverage Django's built-in admin interface
- Use Django's migration system for schema changes
""")

    if "pytest" in frameworks:
        notes.append("""
### pytest

- Use fixtures for test setup and teardown
- Parametrize tests to cover multiple cases
- Use descriptive test names: `test_<function>_<scenario>_<expected>`
- Run tests with: `pytest -v`
""")

    if "pandas" in frameworks or "numpy" in frameworks:
        notes.append("""
### Data Science (pandas/numpy)

- Use vectorized operations instead of loops
- Handle missing data explicitly (dropna, fillna)
- Use meaningful column names and document data schemas
- Validate data types and ranges before processing
""")

    return "\n".join(notes) if notes else "No specific framework guidance available."


def _read_project_readme(project_path: Path, max_chars: int = 1500) -> str:
    """
    Read the project's README if one exists, returning a truncated excerpt.

    Used by inference_prompts.build_analyze_prompt to ground the host agent's
    response in real project documentation rather than letting it hallucinate
    from the project name alone.

    Args:
        project_path: Path to the project directory
        max_chars: Maximum characters to return (default: 1500)

    Returns:
        Truncated README content, or empty string if no README found
    """
    # Try common README filenames in order of preference
    for readme_name in ("README.md", "README.rst", "README.txt", "README"):
        readme_path = project_path / readme_name
        if readme_path.exists() and readme_path.is_file():
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Strip BOM if present, truncate to max_chars
                content = content.lstrip('\ufeff').strip()
                if len(content) > max_chars:
                    content = content[:max_chars] + "..."
                return content
            except (OSError, UnicodeDecodeError):
                continue

    return ""


def _stack_info_to_context(
    stack_info: StackInfo,
    project_path: Path,
    target: str = "bob",
) -> GenerationContext:
    """
    Adapt a StackInfo (analyze mode) into a GenerationContext.

    Does NOT fill the inference fields (intro_prose, skill_content,
    agents_context) — those come from the host agent via Phase 2.

    Args:
        stack_info: Result of praxis.detect.detect_stack()
        project_path: Path to the analyzed project
        target: Output target ("bob", "claude-code", or "cursor")
    """
    return GenerationContext(
        project_name=project_path.name,
        stack_name=stack_info.stack_name,
        frameworks=stack_info.frameworks,
        dependencies=stack_info.dependencies,
        python_files_count=stack_info.python_files_count,
        grounding_context=_read_project_readme(project_path),
        grounding_source_label="README",
        mode="analyze",
        target=target,
    )


def _build_placeholders(context: GenerationContext) -> dict:
    """
    Build the shared placeholders dict used by all per-target templates.

    Same field set for every target. Each target's template references the
    subset it cares about; Python's str.format() ignores unused keys, so
    extra fields here are harmless.
    """
    generation_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    frameworks_list = _format_frameworks_list(context.frameworks)
    dependencies_list = _format_dependencies_list(context.dependencies)

    methodology_short = _render_methodology_short()
    methodology_full = _render_methodology_full()
    methodology_enforcement = _render_methodology_enforcement()

    framework_notes = _generate_framework_notes(context.frameworks)

    # Sanitize the host-agent-provided fields before they hit the templates.
    intro_prose = _sanitize_inference_output(context.intro_prose)
    skill_content = _sanitize_inference_output(context.skill_content)
    agents_context = _sanitize_inference_output(context.agents_context)

    # Build clarifying questions block for plan mode
    if context.mode == "plan" and context.clarifying_questions:
        clarifying_questions_block = (
            "\n## Open Questions for the Developer\n\n"
            "The planning document didn't specify these. Ask the developer at "
            "session start:\n\n"
        )
        for q in context.clarifying_questions:
            clarifying_questions_block += f"- {q}\n"
    else:
        clarifying_questions_block = ""

    # The "granite_*" key names are kept verbatim because the existing Bob
    # templates reference them as {granite_intro_prose}, etc. The Claude Code
    # and Cursor placeholder templates added in 4.2 use the same names for
    # consistency. Renaming the keys is template-side work, deferred.
    return {
        "project_name": context.project_name,
        "stack_name": context.stack_name,
        "generation_date": generation_date,
        "frameworks_list": frameworks_list,
        "dependencies_list": dependencies_list,
        "python_files_count": str(context.python_files_count),
        "methodology_principles_short": methodology_short,
        "methodology_principles_full": methodology_full,
        "methodology_enforcement": methodology_enforcement,
        "granite_intro_prose": intro_prose,
        "granite_skill_content": skill_content,
        "granite_agents_context": agents_context,
        "framework_specific_notes": framework_notes,
        "clarifying_questions_block": clarifying_questions_block,
    }


def _render_template_set(
    templates_dir: Path,
    template_files: dict,
    output_dir: Path,
    placeholders: dict,
) -> list[Path]:
    """
    Load each template file, render with placeholders, write to output_dir.

    Args:
        templates_dir: Directory holding the .template source files
        template_files: Mapping of {output_filename: template_filename}
        output_dir: Directory to write the rendered files into
        placeholders: Substitution map for str.format()

    Returns:
        List of output file paths actually written, in template_files order.
    """
    output_paths = []
    for output_name, template_name in template_files.items():
        template_path = templates_dir / template_name
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        rendered = content.format(**placeholders)
        output_path = output_dir / output_name
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        output_paths.append(output_path)
    return output_paths


def _generate_bob_outputs(
    output_root_path: Path,
    context: GenerationContext,
    placeholders: dict,
) -> list[Path]:
    """
    Render the six Bob configuration files into <root>/praxis_output/.
    """
    output_dir = output_root_path / "praxis_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    templates_dir = Path(__file__).parent / "templates" / "bob"
    template_files = {
        "AGENTS.md": "AGENTS.md.template",
        "PRAXIS_CONTRACT.md": "PRAXIS_CONTRACT.md.template",
        "python_skill.md": "python_skill.md.template",
        "methodology_skill.md": "methodology_skill.md.template",
        ".bobignore": "bobignore.template",
        "custom_mode.md": "custom_mode.md.template",
    }

    return _render_template_set(templates_dir, template_files, output_dir, placeholders)


def _generate_claude_code_outputs(
    output_root_path: Path,
    context: GenerationContext,
    placeholders: dict,
) -> list[Path]:
    """
    Render the single Claude Code CLAUDE.md into <root>/.

    Claude Code reads CLAUDE.md from the project root, so we write directly
    to output_root_path without a praxis_output/ subdirectory.
    """
    output_dir = output_root_path
    output_dir.mkdir(parents=True, exist_ok=True)

    templates_dir = Path(__file__).parent / "templates" / "claude_code"
    template_files = {
        "CLAUDE.md": "CLAUDE.md.template",
    }

    return _render_template_set(templates_dir, template_files, output_dir, placeholders)


def _generate_cursor_outputs(
    output_root_path: Path,
    context: GenerationContext,
    placeholders: dict,
) -> list[Path]:
    """
    Render the two Cursor rule files into <root>/.cursor/rules/.

    Cursor reads rules from .cursor/rules/, so we create that nested directory
    under output_root_path if it doesn't exist.
    """
    output_dir = output_root_path / ".cursor" / "rules"
    output_dir.mkdir(parents=True, exist_ok=True)

    templates_dir = Path(__file__).parent / "templates" / "cursor"
    template_files = {
        "methodology.mdc": "methodology.mdc.template",
        "python.mdc": "python.mdc.template",
    }

    return _render_template_set(templates_dir, template_files, output_dir, placeholders)


def generate_outputs(
    output_root_path: Path,
    context: GenerationContext,
) -> list[Path]:
    """
    Generate target-specific configuration files from a fully-populated context.

    Pure templating: this function performs no LLM calls. All host-agent
    content must already be present on the context (intro_prose, skill_content,
    agents_context). The caller (typically cli.py::generate_command) is
    responsible for populating those from the Phase 1 bob_inference JSON.

    Dispatches on context.target:
      - "bob"         → <root>/praxis_output/ (6 files)
      - "claude-code" → <root>/CLAUDE.md (1 file)
      - "cursor"      → <root>/.cursor/rules/*.mdc (2 files)

    Args:
        output_root_path: Directory under which the target's files are written
        context: Unified context with target, mode, and inference fields filled

    Returns:
        List of paths to generated output files

    Raises:
        ValueError: If context.target is not one of ALLOWED_TARGETS
        NotImplementedError: If stack is not Python (v1 limitation)
        OSError: If template files cannot be read or output cannot be written
    """
    # Validate target up front so the failure mode is clear
    if context.target not in ALLOWED_TARGETS:
        raise ValueError(
            f"Unsupported target: {context.target!r}. "
            f"Allowed: {list(ALLOWED_TARGETS)}"
        )

    # v1 limitation: only Python stack supported
    if context.stack_name != "Python":
        raise NotImplementedError(
            f"Only Python stack is supported in v1. "
            f"Detected stack: {context.stack_name}"
        )

    # Build the shared placeholders dict once; pass to whichever per-target
    # renderer applies.
    placeholders = _build_placeholders(context)

    if context.target == "bob":
        return _generate_bob_outputs(output_root_path, context, placeholders)
    elif context.target == "claude-code":
        return _generate_claude_code_outputs(output_root_path, context, placeholders)
    elif context.target == "cursor":
        return _generate_cursor_outputs(output_root_path, context, placeholders)
    else:
        # Defensive: should be unreachable thanks to the validation above
        raise ValueError(f"Unsupported target: {context.target!r}")
