"""
Praxis generation engine.

Assembles templates with detected stack information and Granite-generated
content to produce tailored Bob IDE configuration files.
"""

from datetime import datetime
from pathlib import Path

from praxis.detect import StackInfo
from praxis.granite import generate as granite_generate
from praxis.methodology import METHODOLOGY_PRINCIPLES


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


def generate_outputs(project_path: Path, stack_info: StackInfo) -> list[Path]:
    """
    Generate Bob IDE configuration files for a project.
    
    Loads templates, calls Granite for content generation, assembles final
    output files, and writes them to <project_path>/praxis_output/.
    
    Args:
        project_path: Path to the project directory
        stack_info: Detected stack information
        
    Returns:
        List of paths to generated output files
        
    Raises:
        NotImplementedError: If stack is not Python (Phase 1 limitation)
        OSError: If template files cannot be read or output cannot be written
    """
    # Phase 1 limitation: only Python stack supported
    if stack_info.stack_name != "Python":
        raise NotImplementedError(
            f"Only Python stack is supported in Phase 1. "
            f"Detected stack: {stack_info.stack_name}"
        )
    
    # Determine output directory
    output_dir = project_path / "praxis_output"
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
    project_name = project_path.name
    generation_date = datetime.utcnow().strftime("%Y-%m-%d")
    frameworks_list = _format_frameworks_list(stack_info.frameworks)
    dependencies_list = _format_dependencies_list(stack_info.dependencies)
    
    # Render methodology in three forms
    methodology_short = _render_methodology_short()
    methodology_full = _render_methodology_full()
    methodology_enforcement = _render_methodology_enforcement()
    
    # Generate framework-specific notes
    framework_notes = _generate_framework_notes(stack_info.frameworks)
    
    # Make Granite calls for content generation
    print("  Calling Granite for PRAXIS_CONTRACT.md introduction...")
    granite_intro_prompt = (
        f"Write a 2-3 paragraph introduction for a project collaboration contract. "
        f"The project is named '{project_name}'. It uses {stack_info.stack_name} as its tech stack. "
        f"Detected frameworks: {frameworks_list}. Detected dependencies: {dependencies_list}. "
        f"The introduction should be written in second person addressing 'Bob' (an AI development partner), "
        f"explaining how Bob will collaborate with the developer on this specific project. "
        f"Mention the detected frameworks by name. Keep it professional, not flowery. "
        f"Output just the introduction prose, no headers, no meta-commentary."
    )
    granite_intro_prose = granite_generate(granite_intro_prompt, max_tokens=300)
    
    print("  Calling Granite for python_skill.md best practices...")
    granite_skill_prompt = (
        f"Write Python development best practices tailored to a project using these frameworks: {frameworks_list}. "
        f"Detected dependencies: {dependencies_list}. "
        f"Output 5-8 bullet points covering Python-specific conventions relevant to this exact dependency set. "
        f"If pytest is detected, include a bullet about test conventions. "
        f"If Flask or FastAPI is detected, include a bullet about web framework patterns. "
        f"If pandas/numpy is detected, include a bullet about data handling. "
        f"Output ONLY the bullet points, no preamble, no header, no closing."
    )
    granite_skill_content = granite_generate(granite_skill_prompt, max_tokens=400)
    
    print("  Calling Granite for AGENTS.md project context...")
    granite_agents_prompt = (
        f"Write a brief 2-3 sentence project description for a project named '{project_name}'. "
        f"It is a {stack_info.stack_name} project. Detected frameworks: {frameworks_list}. "
        f"The description should help an AI development partner understand the project's nature at a glance. "
        f"Output ONLY the description, no headers or meta-commentary."
    )
    granite_agents_context = granite_generate(granite_agents_prompt, max_tokens=150)
    
    # Build placeholder dictionary
    placeholders = {
        "project_name": project_name,
        "stack_name": stack_info.stack_name,
        "generation_date": generation_date,
        "frameworks_list": frameworks_list,
        "dependencies_list": dependencies_list,
        "python_files_count": str(stack_info.python_files_count),
        "methodology_principles_short": methodology_short,
        "methodology_principles_full": methodology_full,
        "methodology_enforcement": methodology_enforcement,
        "granite_intro_prose": granite_intro_prose.strip(),
        "granite_skill_content": granite_skill_content.strip(),
        "granite_agents_context": granite_agents_context.strip(),
        "framework_specific_notes": framework_notes,
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

# Made with Bob
