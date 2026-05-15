"""
Praxis generation engine.

Assembles templates with detected stack information and Granite-generated
content to produce tailored Bob IDE configuration files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone

from praxis.detect import StackInfo
from praxis.plan import PlanInfo
from praxis.granite import generate as granite_generate
from praxis.methodology import METHODOLOGY_PRINCIPLES


__all__ = [
    "generate_outputs",
    "_stack_info_to_context",
    "_plan_info_to_context",
    "GenerationContext",
]


@dataclass
class GenerationContext:
    """
    Unified input for the generation engine.
    
    Both StackInfo (analyze mode) and PlanInfo (plan mode) are adapted into
    this shape. Templates only see GenerationContext, not the source type.
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
    
    # Grounding context for Granite prompts (README for analyze, source doc for plan)
    grounding_context: str = ""
    grounding_source_label: str = ""  # "README" or "planning document"
    
    # Mode flag for template branching
    mode: str = "analyze"  # "analyze" or "plan"


def _format_frameworks_list(frameworks: list[str]) -> str:
    """Format frameworks list for display."""
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
    Read the project's README.md if it exists, returning a truncated excerpt.
    
    Provides grounding context for Granite prose generation so the model
    doesn't hallucinate the project's purpose from the name alone.
    
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


def _stack_info_to_context(stack_info: StackInfo, project_path: Path) -> GenerationContext:
    """Adapt StackInfo (analyze mode) into a GenerationContext."""
    return GenerationContext(
        project_name=project_path.name,
        stack_name=stack_info.stack_name,
        frameworks=stack_info.frameworks,
        dependencies=stack_info.dependencies,
        python_files_count=stack_info.python_files_count,
        grounding_context=_read_project_readme(project_path),
        grounding_source_label="README",
        mode="analyze",
    )


def _plan_info_to_context(plan_info: PlanInfo, doc_path: Path) -> GenerationContext:
    """Adapt PlanInfo (plan mode) into a GenerationContext."""
    # Use the doc's filename (without extension) as project_name, since
    # there's no project directory yet
    project_name = doc_path.stem
    
    return GenerationContext(
        project_name=project_name,
        stack_name=plan_info.inferred_stack,
        frameworks=plan_info.inferred_frameworks,
        project_purpose=plan_info.project_purpose,
        features=plan_info.features,
        integrations=plan_info.integrations,
        clarifying_questions=plan_info.clarifying_questions,
        grounding_context=plan_info.source_doc_excerpt,
        grounding_source_label="planning document",
        mode="plan",
    )


def generate_outputs(
    output_root_path: Path,
    context: GenerationContext,
) -> list[Path]:
    """
    Generate Bob IDE configuration files from a GenerationContext.
    
    Args:
        output_root_path: Directory where praxis_output/ will be created
        context: Unified context (from either StackInfo or PlanInfo)
    
    Returns:
        List of paths to generated output files
    
    Raises:
        NotImplementedError: If stack is not Python (Phase 1 limitation)
        OSError: If template files cannot be read or output cannot be written
    """
    # Phase 1 limitation: only Python stack supported
    if context.stack_name != "Python":
        raise NotImplementedError(
            f"Only Python stack is supported in Phase 1. "
            f"Detected stack: {context.stack_name}"
        )
    
    # Determine output directory
    output_dir = output_root_path / "praxis_output"
    output_dir.mkdir(exist_ok=True)
    
    # Load templates
    templates_dir = Path(__file__).parent / "templates"
    templates = {}
    template_files = {
        "AGENTS.md": "AGENTS.md.template",
        "PRAXIS_CONTRACT.md": "PRAXIS_CONTRACT.md.template",
        "python_skill.md": "python_skill.md.template",
        "methodology_skill.md": "methodology_skill.md.template",
        ".bobignore": "bobignore.template",
        "custom_mode.md": "custom_mode.md.template",
    }
    
    for output_name, template_name in template_files.items():
        template_path = templates_dir / template_name
        with open(template_path, "r", encoding="utf-8") as f:
            templates[output_name] = f.read()
    
    # Prepare common placeholders
    project_name = context.project_name
    generation_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    frameworks_list = _format_frameworks_list(context.frameworks)
    dependencies_list = _format_dependencies_list(context.dependencies)
    
    # Render methodology in three forms
    methodology_short = _render_methodology_short()
    methodology_full = _render_methodology_full()
    methodology_enforcement = _render_methodology_enforcement()
    
    # Generate framework-specific notes
    framework_notes = _generate_framework_notes(context.frameworks)
    
    # Build grounding context block (works for both README and planning doc)
    if context.grounding_context:
        if context.mode == "plan":
            grounding_block = (
                f"\n\nThis is a planning document for a project that doesn't yet exist. "
                f"Use it as ground truth for what the project will do.\n"
                f"Planning document excerpt:\n---\n{context.grounding_context}\n---"
            )
        else:
            grounding_block = (
                f"\n\nProject {context.grounding_source_label} excerpt (use this as ground "
                f"truth about what the project actually does — do not invent a different "
                f"purpose):\n---\n{context.grounding_context}\n---"
            )
    else:
        grounding_block = (
            f"\n\nNo {context.grounding_source_label} available. Describe the project "
            f"conservatively based only on its name, stack, and frameworks. Do not invent."
        )
    
    # Shared tone constraint for all prose-generation prompts
    tone_rules = (
        "Tone rules: plain, direct prose. No corporate language. Do not use phrases "
        "like 'embark on', 'forge a partnership', 'shape the future', 'exceed "
        "expectations', 'ambitious endeavor', 'cutting-edge', 'leveraging', "
        "'pioneering'. Sound like a competent engineer briefing a coworker, not a "
        "CEO opening a keynote."
    )
    
    # Plan-mode specific additions for Granite prompts
    if context.mode == "plan":
        plan_extras = (
            f"\nDetected features: {', '.join(context.features) if context.features else 'none specified'}. "
            f"Detected integrations: {', '.join(context.integrations) if context.integrations else 'none specified'}."
        )
    else:
        plan_extras = ""
    
    # Make Granite calls for content generation
    print("  Calling Granite for PRAXIS_CONTRACT.md introduction...")
    granite_intro_prompt = (
        f"Write 2 short paragraphs (4-5 sentences total) introducing how Bob (an AI "
        f"development partner) will work on the '{project_name}' project. "
        f"Stack: {context.stack_name}. Detected frameworks: {frameworks_list}. "
        f"Detected dependencies: {dependencies_list}.{plan_extras}\n\n"
        f"Address Bob in second person. Mention the detected frameworks or "
        f"dependencies concretely. Focus on what Bob's collaboration will involve "
        f"day-to-day, not abstract goals.\n\n"
        f"{tone_rules}"
        f"{grounding_block}\n\n"
        f"Output only the prose. No headers, no meta-commentary, no 'Dear Bob' "
        f"salutation, no signature."
    )
    granite_intro_prose = granite_generate(granite_intro_prompt, max_tokens=300)
    
    print("  Calling Granite for python_skill.md best practices...")
    granite_skill_prompt = (
        f"Write Python development best practices tailored to a project using these "
        f"frameworks: {frameworks_list}. Detected dependencies: {dependencies_list}. "
        f"Output 5-8 bullet points covering Python-specific conventions relevant to "
        f"this exact dependency set. "
        f"If pytest is detected, include a bullet about test conventions. "
        f"If Flask or FastAPI is detected, include a bullet about web framework patterns. "
        f"If pandas/numpy is detected, include a bullet about data handling. "
        f"Output ONLY the bullet points, no preamble, no header, no closing."
    )
    granite_skill_content = granite_generate(granite_skill_prompt, max_tokens=400)
    
    print("  Calling Granite for AGENTS.md project context...")
    granite_agents_prompt = (
        f"Write a brief 2-3 sentence factual description of the '{project_name}' "
        f"project for an AI development partner to read at session start. "
        f"Stack: {context.stack_name}. Detected frameworks: {frameworks_list}.\n\n"
        f"The description should answer: what does this project do? Be specific and "
        f"factual. If you don't know what the project does, say so plainly instead "
        f"of inventing a purpose.\n\n"
        f"{tone_rules}"
        f"{grounding_block}\n\n"
        f"Output ONLY the description prose, no headers or meta-commentary."
    )
    granite_agents_context = granite_generate(granite_agents_prompt, max_tokens=150)
    
    # Build clarifying questions block for plan mode
    if context.mode == "plan" and context.clarifying_questions:
        clarifying_questions_block = "\n## Open Questions for the Developer\n\nThe planning document didn't specify these. Ask the developer at session start:\n\n"
        for q in context.clarifying_questions:
            clarifying_questions_block += f"- {q}\n"
    else:
        clarifying_questions_block = ""
    
    # Build placeholder dictionary
    placeholders = {
        "project_name": project_name,
        "stack_name": context.stack_name,
        "generation_date": generation_date,
        "frameworks_list": frameworks_list,
        "dependencies_list": dependencies_list,
        "python_files_count": str(context.python_files_count),
        "methodology_principles_short": methodology_short,
        "methodology_principles_full": methodology_full,
        "methodology_enforcement": methodology_enforcement,
        "granite_intro_prose": granite_intro_prose.strip(),
        "granite_skill_content": granite_skill_content.strip(),
        "granite_agents_context": granite_agents_context.strip(),
        "framework_specific_notes": framework_notes,
        "clarifying_questions_block": clarifying_questions_block,
    }
    
    # Render and write all templates
    output_paths = []
    for output_name, template_content in templates.items():
        rendered = template_content.format(**placeholders)
        output_path = output_dir / output_name
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        
        output_paths.append(output_path)
    
    return output_paths

