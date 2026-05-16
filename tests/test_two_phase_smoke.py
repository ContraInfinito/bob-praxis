"""
Two-phase handshake smoke test for the Praxis CLI.

Verifies the analyze and plan flows against all three output targets — bob,
claude-code, and cursor — with a synthetic stand-in for the host agent (Bob).
Does NOT call any LLM.

Six paths total: {analyze, plan} × {bob, claude-code, cursor}.

For each path:
  * Phase 1: `praxis context-prompt <mode> <path> --target <target>` and
    parse the JSON.
  * Phase 2: feed a synthetic bob_inference dict (shape depends on mode)
    into `praxis generate --context <json> --output-root <tmpdir>`.
  * Assert the expected files appear in the target's idiomatic location.
  * Spot-check one inference field landed in the right output file.

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


# Where each target's generated files live, relative to <output_root>.
# (subdir, set-of-expected-filenames-inside-subdir)
# Per-target expected outputs. The value is a list of (subdir, files) pairs
# so a single target can produce files in multiple directories (the Bob target
# splits across praxis_output/ and .bob/ since the generated mode YAML must
# live in .bob/ for Bob to auto-discover it on project open).
EXPECTED_OUTPUTS = {
    "bob": [
        (
            Path("praxis_output"),
            {
                "AGENTS.md",
                "PRAXIS_CONTRACT.md",
                "python_skill.md",
                "methodology_skill.md",
                ".bobignore",
            },
        ),
        (Path(".bob"), {"custom_modes.yaml"}),
    ],
    "claude-code": [
        (Path("."), {"CLAUDE.md"}),
    ],
    "cursor": [
        (Path(".cursor") / "rules", {"methodology.mdc", "python.mdc"}),
    ],
}


# Synthetic host-agent inference. None of these strings start with a sanitizer
# prefix, so they should pass through to the templates unchanged.
ANALYZE_INFERENCE = {
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

PLAN_INFERENCE = {
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


def _source_path_for(mode: str) -> Path:
    """Test fixture path for a given mode."""
    if mode == "analyze":
        return REPO_ROOT / "tests" / "sample_python_project"
    elif mode == "plan":
        return REPO_ROOT / "tests" / "sample_planning_doc.md"
    raise AssertionError(f"unknown mode: {mode}")


def _spot_check_content(
    mode: str,
    target: str,
    target_dir: Path,
    inference: dict,
    tmpdir: str,
) -> None:
    """
    Verify one inference-field-to-output-file claim for the given target.

    For bob, also verifies plan-mode clarifying questions land in AGENTS.md
    AND that the generated .bob/custom_modes.yaml is valid Bob mode YAML.
    """
    if target == "bob":
        agents_md = (target_dir / "AGENTS.md").read_text(encoding="utf-8")
        assert inference["agents_context"][:40] in agents_md, (
            "fake agents_context did not land in AGENTS.md"
        )
        praxis_contract = (target_dir / "PRAXIS_CONTRACT.md").read_text(encoding="utf-8")
        assert inference["intro_prose"][:40] in praxis_contract, (
            "fake intro_prose did not land in PRAXIS_CONTRACT.md"
        )
        if mode == "plan":
            assert "Open Questions for the Developer" in agents_md, (
                "missing 'Open Questions' section in plan-mode AGENTS.md"
            )
            for q in inference["clarifying_questions"]:
                assert q in agents_md, f"clarifying question not in AGENTS.md: {q}"

        # Validate the new .bob/custom_modes.yaml — Bob mode YAML schema.
        import yaml
        bob_yaml_path = Path(tmpdir) / ".bob" / "custom_modes.yaml"
        assert bob_yaml_path.is_file(), f"missing {bob_yaml_path}"
        with open(bob_yaml_path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        assert isinstance(doc, dict), "custom_modes.yaml root must be a mapping"
        assert "customModes" in doc and isinstance(doc["customModes"], list), (
            "custom_modes.yaml must have a non-empty customModes list"
        )
        assert len(doc["customModes"]) >= 1, "customModes list is empty"
        entry = doc["customModes"][0]
        for required_key in (
            "slug", "name", "roleDefinition", "whenToUse",
            "groups", "customInstructions",
        ):
            assert required_key in entry, (
                f"custom_modes.yaml missing required key: {required_key}"
            )
        # slug must be the slugified project_name — derived from the source
        # path stem (analyze) or doc filename stem (plan). Both fixtures use
        # underscores, which slugify rewrites as hyphens.
        if mode == "analyze":
            expected_slug = "sample-python-project"
        else:
            expected_slug = "sample-planning-doc"
        assert entry["slug"] == expected_slug, (
            f"slug mismatch: expected {expected_slug!r}, got {entry['slug']!r}"
        )
        # groups must include at least 'read' and 'command'. The generated
        # mode also includes 'edit' (long-term operating mode writes code);
        # we check the lower bound to keep the assertion narrow.
        assert isinstance(entry["groups"], list), "groups must be a list"
        assert "read" in entry["groups"] and "command" in entry["groups"], (
            f"groups must contain read+command, got {entry['groups']}"
        )

    elif target == "claude-code":
        claude_md = (target_dir / "CLAUDE.md").read_text(encoding="utf-8")
        assert inference["agents_context"][:40] in claude_md, (
            "fake agents_context did not land in CLAUDE.md"
        )

    elif target == "cursor":
        python_mdc = (target_dir / "python.mdc").read_text(encoding="utf-8")
        # skill_content for both inference shapes starts with "- " bullets;
        # check a 30-char prefix that's unique per fixture.
        assert inference["skill_content"][:30] in python_mdc, (
            "fake skill_content did not land in cursor python.mdc"
        )


def _run_one_target(mode: str, target: str, inference: dict) -> None:
    """Run Phase 1 + Phase 2 + assertions for one (mode, target) combination."""
    print(f"--- {mode} + target={target} ---")

    source_path = _source_path_for(mode)
    assert source_path.exists(), f"Fixture missing: {source_path}"

    # ---- Phase 1: context-prompt ----
    rc, stdout, stderr = run_cli([
        "context-prompt", mode, str(source_path), "--target", target,
    ])
    assert rc == 0, (
        f"context-prompt mode={mode} target={target} rc={rc}\nstderr:\n{stderr}"
    )

    blob = json.loads(stdout)
    for key in ("prompt_for_bob", "partial_context", "meta"):
        assert key in blob, f"missing top-level key: {key}"
    assert blob["partial_context"]["target"] == target, (
        f"partial_context.target = {blob['partial_context'].get('target')!r}, "
        f"expected {target!r}"
    )
    assert blob["meta"]["target"] == target, (
        f"meta.target = {blob['meta'].get('target')!r}, expected {target!r}"
    )
    assert blob["meta"]["mode"] == mode
    assert blob["meta"]["schema_version"] == "1.0"

    # ---- Phase 2: generate with synthetic bob_inference ----
    context_blob = {
        "partial_context": blob["partial_context"],
        "bob_inference": inference,
        "meta": blob["meta"],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        rc, stdout, stderr = run_cli([
            "generate",
            "--context", json.dumps(context_blob),
            "--output-root", tmpdir,
        ])
        assert rc == 0, (
            f"generate mode={mode} target={target} rc={rc}\nstderr:\n{stderr}"
        )

        # Iterate over each (subdir, expected-files) pair the target produces.
        # Bob splits its output across two directories; the others use one.
        total_files = 0
        subdir_reports = []
        for subdir_rel, expected_files in EXPECTED_OUTPUTS[target]:
            target_dir = Path(tmpdir) / subdir_rel
            assert target_dir.is_dir(), (
                f"missing target output dir {target_dir} for target={target}"
            )
            actual_files = {p.name for p in target_dir.iterdir() if p.is_file()}
            assert actual_files == expected_files, (
                f"target={target} subdir={subdir_rel}: "
                f"expected {expected_files}, got {actual_files}"
            )
            total_files += len(actual_files)
            subdir_label = str(subdir_rel) if str(subdir_rel) != "." else "<root>"
            subdir_reports.append(f"{len(actual_files)} in {subdir_label}")

        # Spot-check that inference content landed in the right output file.
        # The spot-check uses the FIRST subdir as the "primary" target_dir for
        # backwards-compatible per-target assertions. Bob-target specific
        # YAML-validity assertions live inside _spot_check_content.
        primary_dir = Path(tmpdir) / EXPECTED_OUTPUTS[target][0][0]
        _spot_check_content(mode, target, primary_dir, inference, tmpdir)

        print(f"  OK: {total_files} file(s) ({', '.join(subdir_reports)})")


def _run_context_file_smoke(inference: dict) -> None:
    """
    7th path: prove --context-file works as a drop-in for --context.

    Uses analyze + bob (the canonical case) — Phase 1 emits the partial
    context, we assemble the same Phase 2 blob as the inline path, but write
    it to a UTF-8 file and pass the path via --context-file instead of
    --context. Same file set should land in the same locations.
    """
    print("--- analyze + target=bob via --context-file ---")
    source_path = _source_path_for("analyze")
    assert source_path.exists(), f"Fixture missing: {source_path}"

    rc, stdout, stderr = run_cli([
        "context-prompt", "analyze", str(source_path), "--target", "bob",
    ])
    assert rc == 0, f"phase1 (--context-file path) rc={rc}\nstderr:\n{stderr}"
    blob = json.loads(stdout)

    context_blob = {
        "partial_context": blob["partial_context"],
        "bob_inference": inference,
        "meta": blob["meta"],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the context blob to a UTF-8 temp file inside the same tmpdir.
        # Using NO BOM (default for Path.write_text with encoding="utf-8")
        # exercises the happy path. The BOM-strip code in cli.py is exercised
        # implicitly by anyone who writes the file via PowerShell Out-File.
        ctx_path = Path(tmpdir) / "context.json"
        ctx_path.write_text(json.dumps(context_blob), encoding="utf-8")

        rc, stdout, stderr = run_cli([
            "generate",
            "--context-file", str(ctx_path),
            "--output-root", tmpdir,
        ])
        assert rc == 0, f"phase2 via --context-file rc={rc}\nstderr:\n{stderr}"

        total_files = 0
        subdir_reports = []
        for subdir_rel, expected_files in EXPECTED_OUTPUTS["bob"]:
            target_dir = Path(tmpdir) / subdir_rel
            assert target_dir.is_dir(), f"missing {target_dir} via --context-file"
            actual = {p.name for p in target_dir.iterdir() if p.is_file()}
            assert actual == expected_files, (
                f"--context-file path subdir={subdir_rel}: "
                f"expected {expected_files}, got {actual}"
            )
            total_files += len(actual)
            subdir_label = str(subdir_rel) if str(subdir_rel) != "." else "<root>"
            subdir_reports.append(f"{len(actual)} in {subdir_label}")

        print(
            f"  OK: --context-file produced {total_files} file(s) "
            f"({', '.join(subdir_reports)})"
        )


def _run_mutex_smoke() -> None:
    """
    Verify argparse enforces the --context / --context-file mutex correctly:

      * Both flags set  → reject (exit non-zero)
      * Neither flag set → reject (exit non-zero)

    Argparse handles this for free via add_mutually_exclusive_group(required=True);
    these subprocess invocations make the guarantee testable end-to-end so a
    refactor that drops the group is caught immediately.
    """
    print("--- mutex: both flags ---")
    rc, _, _ = run_cli([
        "generate",
        "--context", "{}",
        "--context-file", "nonexistent.json",
        "--output-root", ".",
    ])
    assert rc != 0, "generate should reject both --context and --context-file"
    print("  OK: rejected both")

    print("--- mutex: neither flag ---")
    rc, _, _ = run_cli([
        "generate",
        "--output-root", ".",
    ])
    assert rc != 0, "generate should reject neither --context nor --context-file"
    print("  OK: rejected neither")


def main() -> int:
    print("=== analyze paths (3 targets) ===")
    for target in ("bob", "claude-code", "cursor"):
        _run_one_target("analyze", target, ANALYZE_INFERENCE)

    print()
    print("=== plan paths (3 targets) ===")
    for target in ("bob", "claude-code", "cursor"):
        _run_one_target("plan", target, PLAN_INFERENCE)

    print()
    print("=== --context-file alternative path (1 target) ===")
    _run_context_file_smoke(ANALYZE_INFERENCE)

    print()
    print("=== --context / --context-file mutex (2 checks) ===")
    _run_mutex_smoke()

    print()
    print("All two-phase smoke tests passed (7 paths + 2 mutex checks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
