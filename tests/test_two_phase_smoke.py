"""
Two-phase handshake smoke test for the Praxis CLI.

Verifies the analyze and plan flows end-to-end with a synthetic stand-in for
the host agent (Bob). Does NOT call any LLM — instead it crafts a fake
bob_inference dict in the shape Phase 1's prompt asks for, then feeds it into
Phase 2 and checks that all six output files appear.

Run from the repo root:

    python tests/test_two_phase_smoke.py

Exits 0 on success, non-zero on any assertion failure.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.resolve()


def run_cli(args: list[str]) -> tuple[int, str, str]:
    """
    Run `python -m praxis ...` as a subprocess.

    Returns (returncode, stdout, stderr). cwd is the repo root so `python -m
    praxis` resolves the package correctly.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "praxis", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(REPO_ROOT),
    )
    return proc.returncode, proc.stdout, proc.stderr


EXPECTED_OUTPUT_FILES = {
    "AGENTS.md",
    "PRAXIS_CONTRACT.md",
    "python_skill.md",
    "methodology_skill.md",
    ".bobignore",
    "custom_mode.md",
}


def test_analyze_mode() -> None:
    """Phase 1 + Phase 2 for analyze mode against tests/sample_python_project."""
    print("=== analyze mode ===")
    project_path = REPO_ROOT / "tests" / "sample_python_project"
    assert project_path.is_dir(), f"Fixture missing: {project_path}"

    # ---- Phase 1: context-prompt ----
    rc, stdout, stderr = run_cli(["context-prompt", "analyze", str(project_path)])
    assert rc == 0, f"context-prompt analyze rc={rc}\nstderr:\n{stderr}"

    blob = json.loads(stdout)
    for key in ("prompt_for_bob", "partial_context", "meta"):
        assert key in blob, f"missing top-level key: {key}"

    assert isinstance(blob["prompt_for_bob"], str)
    assert isinstance(blob["partial_context"], dict)
    assert isinstance(blob["meta"], dict)

    pc = blob["partial_context"]
    assert pc["mode"] == "analyze"
    assert pc["grounding_source_label"] == "README"
    assert "project_name" in pc and pc["project_name"]
    assert "stack_name" in pc

    assert blob["meta"]["mode"] == "analyze"
    assert blob["meta"]["schema_version"] == "1.0"

    print(
        f"  Phase 1 OK: prompt={len(blob['prompt_for_bob'])} chars, "
        f"stack={pc['stack_name']}, "
        f"frameworks={pc.get('frameworks')}, "
        f"deps={len(pc.get('dependencies', []))}"
    )

    # ---- Phase 2: generate with synthetic bob_inference ----
    fake_inference = {
        "intro_prose": (
            "Bob, on the sample_python_project you'll be working with a minimal "
            "Flask application backed by pytest tests. The app is small enough "
            "to read end-to-end in one sitting.\n\n"
            "Day-to-day, you'll review route additions, help debug failing tests, "
            "and keep the project consistent with Flask conventions."
        ),
        "skill_content": (
            "- Keep Flask route handlers small; push logic into helper functions.\n"
            "- Use the Flask test client (app.test_client()) inside pytest tests.\n"
            "- Run tests with `pytest -v` from the project root.\n"
            "- Store secrets in environment variables, never hardcoded.\n"
            "- Use blueprints once route count exceeds about five handlers."
        ),
        "agents_context": (
            "sample_python_project is a minimal Flask web application with a "
            "single hello-world route, backed by pytest tests. It exists as a "
            "fixture for testing the Praxis CLI itself."
        ),
    }

    context_blob = {
        "partial_context": blob["partial_context"],
        "bob_inference": fake_inference,
        "meta": blob["meta"],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        rc, stdout, stderr = run_cli([
            "generate",
            "--context", json.dumps(context_blob),
            "--output-root", tmpdir,
        ])
        assert rc == 0, f"generate analyze rc={rc}\nstderr:\n{stderr}"

        out_dir = Path(tmpdir) / "praxis_output"
        assert out_dir.is_dir(), f"missing praxis_output dir under {tmpdir}"

        actual_files = {p.name for p in out_dir.iterdir()}
        assert actual_files == EXPECTED_OUTPUT_FILES, (
            f"expected {EXPECTED_OUTPUT_FILES}, got {actual_files}"
        )

        # Spot-check that the inference content was injected into the templates
        agents_md = (out_dir / "AGENTS.md").read_text(encoding="utf-8")
        assert "sample_python_project is a minimal Flask web application" in agents_md, (
            "fake agents_context did not land in AGENTS.md"
        )

        praxis_contract = (out_dir / "PRAXIS_CONTRACT.md").read_text(encoding="utf-8")
        assert "Bob, on the sample_python_project" in praxis_contract, (
            "fake intro_prose did not land in PRAXIS_CONTRACT.md"
        )

        print(f"  Phase 2 OK: {len(actual_files)} files generated in {out_dir}")

    print("  analyze mode: PASS\n")


def test_plan_mode() -> None:
    """Phase 1 + Phase 2 for plan mode against tests/sample_planning_doc.md."""
    print("=== plan mode ===")
    doc_path = REPO_ROOT / "tests" / "sample_planning_doc.md"
    assert doc_path.is_file(), f"Fixture missing: {doc_path}"

    # ---- Phase 1: context-prompt ----
    rc, stdout, stderr = run_cli(["context-prompt", "plan", str(doc_path)])
    assert rc == 0, f"context-prompt plan rc={rc}\nstderr:\n{stderr}"

    blob = json.loads(stdout)
    for key in ("prompt_for_bob", "partial_context", "meta"):
        assert key in blob, f"missing top-level key: {key}"

    pc = blob["partial_context"]
    assert pc["mode"] == "plan"
    assert pc["grounding_source_label"] == "planning document"
    assert "project_name" in pc and pc["project_name"]
    # In plan mode, stack_name and frameworks come from bob_inference, not partial_context
    assert "stack_name" not in pc, "plan-mode partial_context should NOT pre-populate stack_name"
    assert "frameworks" not in pc, "plan-mode partial_context should NOT pre-populate frameworks"

    assert blob["meta"]["mode"] == "plan"
    assert blob["meta"]["schema_version"] == "1.0"

    print(
        f"  Phase 1 OK: prompt={len(blob['prompt_for_bob'])} chars, "
        f"project_name={pc['project_name']}, "
        f"grounding_chars={len(pc.get('grounding_context', ''))}"
    )

    # ---- Phase 2: generate with synthetic plan-mode bob_inference ----
    fake_inference = {
        "inferred_stack": "Python",
        "inferred_frameworks": ["Flask", "pytest"],
        "project_purpose": (
            "A planning document for a habit-tracking REST API built with Flask "
            "and tested with pytest."
        ),
        "features": [
            "user signup and login",
            "create and edit habits",
            "log daily habit completions",
            "view streak statistics",
        ],
        "integrations": ["PostgreSQL", "SendGrid"],
        "clarifying_questions": [
            "What authentication scheme should be used for the API?",
            "Is there a preferred deployment target (Heroku, Fly.io, EC2)?",
            "What level of test coverage is required before merging?",
        ],
        "intro_prose": (
            "Bob, the sample_planning_doc project will be a Flask-based habit "
            "tracker exposed as a REST API, with pytest covering both unit and "
            "integration paths. The codebase doesn't exist yet — you'll be "
            "involved from the first commit forward.\n\n"
            "Day-to-day, you'll help scaffold the Flask app structure, write "
            "endpoint tests with pytest, and surface decisions the planning "
            "document didn't pin down."
        ),
        "skill_content": (
            "- Start each new endpoint with a failing pytest test before writing the handler.\n"
            "- Use Flask blueprints from day one; the app will grow.\n"
            "- Store all secrets in environment variables and document each in README.\n"
            "- Keep authentication logic in a single module.\n"
            "- Use `pytest -v` and add coverage tracking early."
        ),
        "agents_context": (
            "sample_planning_doc describes a Python web application using Flask "
            "with pytest tests, intended as a habit-tracking REST API. The "
            "project is in planning phase — no code exists yet."
        ),
    }

    context_blob = {
        "partial_context": blob["partial_context"],
        "bob_inference": fake_inference,
        "meta": blob["meta"],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        rc, stdout, stderr = run_cli([
            "generate",
            "--context", json.dumps(context_blob),
            "--output-root", tmpdir,
        ])
        assert rc == 0, f"generate plan rc={rc}\nstderr:\n{stderr}"

        out_dir = Path(tmpdir) / "praxis_output"
        assert out_dir.is_dir(), f"missing praxis_output dir under {tmpdir}"

        actual_files = {p.name for p in out_dir.iterdir()}
        assert actual_files == EXPECTED_OUTPUT_FILES, (
            f"expected {EXPECTED_OUTPUT_FILES}, got {actual_files}"
        )

        agents_md = (out_dir / "AGENTS.md").read_text(encoding="utf-8")
        assert "Open Questions for the Developer" in agents_md, (
            "missing 'Open Questions' section in plan-mode AGENTS.md"
        )
        for question in fake_inference["clarifying_questions"]:
            assert question in agents_md, f"clarifying question not in AGENTS.md: {question}"

        praxis_contract = (out_dir / "PRAXIS_CONTRACT.md").read_text(encoding="utf-8")
        assert "Flask" in praxis_contract and "pytest" in praxis_contract, (
            "inferred frameworks (Flask, pytest) did not land in PRAXIS_CONTRACT.md"
        )

        print(
            f"  Phase 2 OK: {len(actual_files)} files generated, "
            f"{len(fake_inference['clarifying_questions'])} clarifying questions in AGENTS.md"
        )

    print("  plan mode: PASS\n")


def main() -> int:
    test_analyze_mode()
    test_plan_mode()
    print("All two-phase smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
