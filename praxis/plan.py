"""
Planning document parser for Praxis.

Extracts structured intent from markdown/text planning documents using
Granite LLM inference. Returns a PlanInfo dataclass that feeds into the
generation engine.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from praxis.granite import generate as granite_generate


@dataclass
class PlanInfo:
    """
    Structured intent extracted from a planning document.
    
    Mirrors StackInfo's role for plan mode: a structured artifact that
    feeds into the generation engine.
    """
    inferred_stack: str  # "Python" or "Generic" (Unity deferred to v2)
    inferred_frameworks: list[str] = field(default_factory=list)  # Same vocabulary as detect.py
    project_purpose: str = ""  # 1-2 sentence factual description
    features: list[str] = field(default_factory=list)  # 3-7 short phrases
    integrations: list[str] = field(default_factory=list)  # External systems mentioned
    clarifying_questions: list[str] = field(default_factory=list)  # Ambiguities for the user
    source_doc_excerpt: str = ""  # First 1500 chars of the doc, for downstream use


def parse_planning_doc(doc_path: Path) -> PlanInfo:
    """
    Parse a planning document and return structured intent.
    
    Uses Granite to extract project purpose, inferred stack, features,
    integrations, and clarifying questions. Returns a PlanInfo.
    
    Args:
        doc_path: Path to the planning document (.md, .markdown, or .txt)
    
    Returns:
        PlanInfo with extracted structured intent
    
    Raises:
        FileNotFoundError: If doc_path doesn't exist
        ValueError: If doc_path is not a file or has unsupported extension
        RuntimeError: If Granite returns malformed JSON twice in a row
    """
    # Step 1: Validate input
    if not doc_path.exists():
        raise FileNotFoundError(f"Planning document not found: {doc_path}")
    
    if not doc_path.is_file():
        raise ValueError(f"Path is not a file: {doc_path}")
    
    allowed_extensions = {".md", ".markdown", ".txt"}
    if doc_path.suffix.lower() not in allowed_extensions:
        raise ValueError(
            f"Unsupported file extension: {doc_path.suffix}. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Step 2: Read the document
    try:
        content = doc_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback to latin-1 like detect.py does
        content = doc_path.read_text(encoding="latin-1")
    
    # Strip BOM if present
    if content.startswith("\ufeff"):
        content = content[1:]
    
    # Cap at 8000 characters
    original_content = content
    if len(content) > 8000:
        content = content[:8000] + "\n\n...[document truncated]"
    
    # Step 3: Build the Granite prompt
    prompt = f"""You are analyzing a planning document for a software project. Read the 
document below and return a JSON object describing the project's intent.

The JSON must match this exact schema:
{{
  "inferred_stack": "Python" | "Generic",
  "inferred_frameworks": ["Flask" | "FastAPI" | "Django" | "pandas" | "numpy" | "pytest"],
  "project_purpose": "1-2 sentence factual description of what the project does",
  "features": ["short phrase", "short phrase", ...],
  "integrations": ["service name", "service name", ...],
  "clarifying_questions": ["question 1", "question 2", ...]
}}

Rules:
- inferred_stack: "Python" if the document mentions Python, Flask, FastAPI, 
  Django, pandas, numpy, pytest, or any Python-specific concept. Otherwise 
  "Generic".
- inferred_frameworks: ONLY from the listed set above. Do not invent 
  framework names. Empty list if none apply.
- project_purpose: 1-2 sentences. Be specific. No marketing language. If 
  the document is too vague, write "Purpose unclear from planning document."
- features: 3-7 short phrases. Each phrase 3-8 words. Concrete features, 
  not abstract goals.
- integrations: external systems explicitly mentioned (databases, APIs, 
  third-party services). Empty list if none mentioned.
- clarifying_questions: 0-5 questions about things the document did NOT 
  specify but a developer would need to know. Examples: "What database 
  should be used?", "Is authentication required?", "What deployment target?"
  Empty list ONLY if the document is fully specified — be honest, most 
  planning docs have gaps.

Output ONLY the JSON object. No preamble. No code fences. No explanation 
before or after. Start with {{ and end with }}.

Planning document:
---
{content}
---"""

    # Step 4: Call Granite, parse JSON
    response = granite_generate(prompt, max_tokens=1000)
    
    # Strip code fences if present (Granite sometimes adds them despite instructions)
    def strip_code_fences(text: str) -> str:
        """Remove markdown code fences from JSON response."""
        text = text.strip()
        # Remove opening fence
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        # Remove closing fence
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
    
    # Try to parse JSON
    parsed_json: dict[str, Any] | None = None
    parse_error: str | None = None
    
    try:
        cleaned_response = strip_code_fences(response)
        parsed_json = json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        parse_error = str(e)
        
        # Retry once with follow-up prompt
        retry_prompt = f"""Your previous response was not valid JSON. The parse error was: {parse_error}

Return ONLY a valid JSON object matching the schema. No preamble, no code
fences, no explanation. Just the JSON. Try again."""
        
        retry_response = granite_generate(retry_prompt, max_tokens=1000)
        
        try:
            cleaned_retry = strip_code_fences(retry_response)
            parsed_json = json.loads(cleaned_retry)
        except json.JSONDecodeError as e2:
            raise RuntimeError(
                f"Granite returned malformed JSON twice.\n"
                f"First error: {parse_error}\n"
                f"First response: {response[:200]}...\n"
                f"Second error: {str(e2)}\n"
                f"Second response: {retry_response[:200]}..."
            )
    
    # Step 5: Validate the parsed JSON
    if parsed_json is None:
        raise RuntimeError("Failed to parse JSON from Granite response")
    
    # Extract and validate fields with defaults
    inferred_stack = parsed_json.get("inferred_stack", "Generic")
    if inferred_stack not in {"Python", "Generic"}:
        inferred_stack = "Generic"
    
    inferred_frameworks = parsed_json.get("inferred_frameworks", [])
    if not isinstance(inferred_frameworks, list):
        inferred_frameworks = []
    
    project_purpose = parsed_json.get("project_purpose", "")
    if not isinstance(project_purpose, str):
        project_purpose = str(project_purpose)
    
    features = parsed_json.get("features", [])
    if not isinstance(features, list):
        features = []
    
    integrations = parsed_json.get("integrations", [])
    if not isinstance(integrations, list):
        integrations = []
    
    clarifying_questions = parsed_json.get("clarifying_questions", [])
    if not isinstance(clarifying_questions, list):
        clarifying_questions = []
    
    # Step 6: Build and return PlanInfo
    source_doc_excerpt = original_content[:1500]
    
    return PlanInfo(
        inferred_stack=inferred_stack,
        inferred_frameworks=inferred_frameworks,
        project_purpose=project_purpose,
        features=features,
        integrations=integrations,
        clarifying_questions=clarifying_questions,
        source_doc_excerpt=source_doc_excerpt,
    )


if __name__ == "__main__":
    # Self-test: parse a small inline planning doc
    import tempfile
    sample_doc = """# Recipe Sharing API

A REST API for sharing and discovering recipes.

Built with Flask and PostgreSQL. Will use pytest for testing.

## Features
- Users can submit new recipes
- Users can browse and search recipes by ingredient
- Users can rate and comment on recipes

## Integrations
- PostgreSQL for recipe storage
- Stripe for premium subscriptions
"""
    
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(sample_doc)
        doc_path = Path(f.name)
    
    try:
        result = parse_planning_doc(doc_path)
        print(f"Inferred stack: {result.inferred_stack}")
        print(f"Frameworks: {result.inferred_frameworks}")
        print(f"Purpose: {result.project_purpose}")
        print(f"Features: {result.features}")
        print(f"Integrations: {result.integrations}")
        print(f"Clarifying questions: {result.clarifying_questions}")
    finally:
        doc_path.unlink()

# Made with Bob
