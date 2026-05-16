"""
Praxis command-line interface.

Two-phase handshake design (Phase 4-revised):

  Phase 1: `praxis context-prompt <mode> <path>`
      Reads project files / planning doc, builds a prompt for the host agent
      (Bob), prints a JSON blob to stdout containing:
          - prompt_for_bob   the natural-language instruction
          - partial_context  deterministic fields already known
          - meta             schema_version, mode, path

  Phase 2: `praxis generate (--context <json> | --context-file <path>) --output-root <dir>`
      Consumes a JSON blob containing partial_context + bob_inference (the
      host agent's answer) + meta, renders the templates, writes the per-
      target output files under <output-root>. Use --context for short inline
      blobs; use --context-file (preferred on Windows) when the blob has
      characters that fight shell quoting.

The CLI prints status messages to stderr and machine-parseable output (the
Phase 1 JSON, the Phase 2 generated-file-path list) to stdout. This makes the
commands clean to pipe and to consume from inside Bob.
"""

import argparse
import json
import sys
from pathlib import Path


def context_prompt_command(args: argparse.Namespace) -> int:
    """
    Phase 1: read files, build a prompt for the host agent, emit JSON to stdout.

    Args:
        args: Parsed argparse namespace with `mode` and `path`.

    Returns:
        Exit code (0 success, 1 user/IO error, 2 unsupported stack).
    """
    # Late imports so `praxis --help` and `praxis --version` don't pay the cost
    # of loading detect/inference_prompts/generate.
    from praxis.detect import detect_stack
    from praxis.inference_prompts import build_analyze_prompt, build_plan_prompt

    path = Path(args.path).resolve()
    target = args.target

    print(f"Target: {target}", file=sys.stderr)

    if args.mode == "analyze":
        if not path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            return 1
        if not path.is_dir():
            print(f"Error: Path is not a directory: {path}", file=sys.stderr)
            return 1

        print(f"Detecting stack at: {path}", file=sys.stderr)
        try:
            stack_info = detect_stack(path)
            print(f"Detected stack: {stack_info.stack_name}", file=sys.stderr)
            if stack_info.frameworks:
                print(f"Frameworks: {', '.join(stack_info.frameworks)}", file=sys.stderr)

            result = build_analyze_prompt(stack_info, path, target=target)
            # Stdout is reserved for the JSON output so Bob (or any caller)
            # can pipe `praxis context-prompt analyze ./foo | jq` cleanly.
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        except Exception as e:
            print(f"Error during analyze context-prompt: {e}", file=sys.stderr)
            return 1

    elif args.mode == "plan":
        if not path.exists():
            print(f"Error: Planning document does not exist: {path}", file=sys.stderr)
            return 1
        if not path.is_file():
            print(f"Error: Path is not a file: {path}", file=sys.stderr)
            return 1

        allowed_extensions = {".md", ".markdown", ".txt"}
        if path.suffix.lower() not in allowed_extensions:
            print(
                f"Error: Unsupported file extension: {path.suffix}. "
                f"Allowed: {', '.join(sorted(allowed_extensions))}",
                file=sys.stderr,
            )
            return 1

        print(f"Reading planning document: {path}", file=sys.stderr)
        try:
            # Read with UTF-8, fall back to latin-1 (mirrors detect.py behavior)
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = path.read_text(encoding="latin-1")

            # Strip BOM if present
            if content.startswith("\ufeff"):
                content = content[1:]

            result = build_plan_prompt(path, content, target=target)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        except Exception as e:
            print(f"Error during plan context-prompt: {e}", file=sys.stderr)
            return 1

    # argparse `choices=[...]` should make this unreachable, but be defensive.
    print(f"Error: Unknown mode: {args.mode}", file=sys.stderr)
    return 1


def generate_command(args: argparse.Namespace) -> int:
    """
    Phase 2: consume the host agent's answer + partial context, write files.

    Args:
        args: Parsed argparse namespace. Exactly one of `context` (inline JSON
              string) or `context_file` (path to a UTF-8 JSON file) is set;
              argparse's mutually-exclusive group enforces the "exactly one"
              invariant. `output_root` (directory path) is always set.

    Returns:
        Exit code (0 success, 1 user/IO error, 2 unsupported stack).
    """
    # Late imports
    from praxis.generate import GenerationContext, generate_outputs

    # Resolve which flag supplied the JSON. argparse's mutually-exclusive group
    # guarantees exactly one of --context / --context-file is set; we still
    # branch explicitly so the failure mode is obvious in tracebacks.
    if args.context is not None:
        context_source = "inline --context"
        raw_json = args.context
    else:
        file_path = Path(args.context_file)
        if not file_path.exists():
            print(
                f"Error: --context-file does not exist: {file_path}",
                file=sys.stderr,
            )
            return 1
        if not file_path.is_file():
            print(
                f"Error: --context-file is not a regular file: {file_path}",
                file=sys.stderr,
            )
            return 1
        try:
            raw_json = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(
                f"Error: Could not read --context-file {file_path}: {e}",
                file=sys.stderr,
            )
            return 1
        # Strip BOM if present. PowerShell's default Out-File encoding writes
        # a UTF-8 BOM that json.loads() rejects with a useless "Expecting value:
        # line 1 column 1 (char 0)" error. Same idiom as the planning-doc
        # reader above and generate.py's _read_project_readme.
        if raw_json.startswith("\ufeff"):
            raw_json = raw_json[1:]
        context_source = f"--context-file {file_path}"

    # Parse the context JSON blob
    try:
        blob = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"Error: {context_source} is not valid JSON: {e}", file=sys.stderr)
        return 1

    # Validate required top-level keys
    required_keys = {"partial_context", "bob_inference", "meta"}
    missing = required_keys - set(blob.keys())
    if missing:
        print(
            f"Error: --context JSON missing required keys: "
            f"{', '.join(sorted(missing))}",
            file=sys.stderr,
        )
        return 1

    partial_context = blob["partial_context"]
    bob_inference = blob["bob_inference"]
    meta = blob["meta"]

    if not isinstance(partial_context, dict):
        print("Error: partial_context must be a JSON object", file=sys.stderr)
        return 1
    if not isinstance(bob_inference, dict):
        print("Error: bob_inference must be a JSON object", file=sys.stderr)
        return 1
    if not isinstance(meta, dict):
        print("Error: meta must be a JSON object", file=sys.stderr)
        return 1

    # Determine mode: prefer partial_context's mode (set by Phase 1), fall back to meta
    mode = partial_context.get("mode") or meta.get("mode") or "analyze"

    # Determine target. Unlike mode this has no default — Phase 1 always stamps
    # it; if it's missing or invalid the blob is malformed and we reject hard.
    target = partial_context.get("target") or meta.get("target")
    if not target:
        print(
            "Error: target is missing from both partial_context and meta. "
            "Did Phase 1 run with an old version of the CLI?",
            file=sys.stderr,
        )
        return 1
    allowed_targets = {"bob", "claude-code", "cursor"}
    if target not in allowed_targets:
        print(
            f"Error: invalid target {target!r}. "
            f"Allowed: {sorted(allowed_targets)}",
            file=sys.stderr,
        )
        return 1

    # Build the GenerationContext, merging deterministic + inference fields.
    # For analyze mode, stack/frameworks come from partial_context (detected
    # locally during Phase 1). For plan mode, they come from bob_inference
    # (the host agent inferred them from the planning doc).
    if mode == "analyze":
        context = GenerationContext(
            project_name=partial_context.get("project_name", ""),
            stack_name=partial_context.get("stack_name", "Generic"),
            frameworks=list(partial_context.get("frameworks", [])),
            dependencies=list(partial_context.get("dependencies", [])),
            python_files_count=int(partial_context.get("python_files_count", 0)),
            grounding_context=partial_context.get("grounding_context", ""),
            grounding_source_label=partial_context.get("grounding_source_label", "README"),
            mode="analyze",
            target=target,
        )
    elif mode == "plan":
        context = GenerationContext(
            project_name=partial_context.get("project_name", ""),
            stack_name=bob_inference.get("inferred_stack", "Generic"),
            frameworks=list(bob_inference.get("inferred_frameworks", [])),
            project_purpose=bob_inference.get("project_purpose", ""),
            features=list(bob_inference.get("features", [])),
            integrations=list(bob_inference.get("integrations", [])),
            clarifying_questions=list(bob_inference.get("clarifying_questions", [])),
            grounding_context=partial_context.get("grounding_context", ""),
            grounding_source_label=partial_context.get("grounding_source_label", "planning document"),
            mode="plan",
            target=target,
        )
    else:
        print(f"Error: Unknown mode in context: {mode}", file=sys.stderr)
        return 1

    # Fill the host-agent inference fields. These are the same shape for both
    # analyze and plan mode.
    context.intro_prose = bob_inference.get("intro_prose", "")
    context.skill_content = bob_inference.get("skill_content", "")
    context.agents_context = bob_inference.get("agents_context", "")

    # Resolve and prepare output root
    output_root = Path(args.output_root).resolve()
    if not output_root.exists():
        try:
            output_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(
                f"Error: Could not create output root {output_root}: {e}",
                file=sys.stderr,
            )
            return 1

    if not output_root.is_dir():
        print(f"Error: Output root is not a directory: {output_root}", file=sys.stderr)
        return 1

    print(f"Generating output for target={target} in: {output_root}", file=sys.stderr)

    try:
        output_paths = generate_outputs(output_root, context)
        # Stdout: one file path per line, so callers can pipe `... | xargs ls`
        for p in output_paths:
            print(str(p))

        if mode == "plan" and context.clarifying_questions:
            print(
                f"\n{len(context.clarifying_questions)} clarifying questions "
                f"surfaced in AGENTS.md. Ask the developer at session start.",
                file=sys.stderr,
            )

        return 0
    except NotImplementedError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error during generation: {e}", file=sys.stderr)
        return 1


def _force_utf8_io() -> None:
    """
    Force sys.stdout/sys.stderr to UTF-8 on platforms where the default is not.

    Phase 4-revised consumers (Bob, the smoke test, anyone piping the output)
    parse Phase 1's stdout as JSON and expect UTF-8. On Windows, the default
    console code page is often cp1252; without this, em-dashes and other
    non-ASCII characters in the JSON or status messages would corrupt the
    output stream. Wrapped in try/except in case stdout/stderr have been
    monkey-patched to something that doesn't expose `reconfigure`.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def main() -> int:
    """
    Main entry point for the Praxis CLI.

    Parses command-line arguments and dispatches to the appropriate subcommand.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    _force_utf8_io()

    parser = argparse.ArgumentParser(
        prog="praxis",
        description="A methodology transfer tool for IBM Bob IDE",
        epilog="For more information, see: https://github.com/ContraInfinito/bob-praxis",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands",
    )

    # 'context-prompt' subcommand (Phase 1)
    cp_parser = subparsers.add_parser(
        "context-prompt",
        help="Phase 1: read files and emit a JSON prompt for the host agent",
        description=(
            "Reads the project files (analyze) or planning document (plan), builds "
            "a natural-language prompt for the host agent (e.g., Bob) to answer, "
            "and prints the prompt plus deterministic partial context as a JSON "
            "object on stdout. Status messages go to stderr."
        ),
    )
    cp_parser.add_argument(
        "mode",
        choices=["analyze", "plan"],
        help="Operating mode: analyze (existing codebase) or plan (planning document)",
    )
    cp_parser.add_argument(
        "path",
        type=str,
        help="Path to the project directory (analyze) or planning document (plan)",
    )
    cp_parser.add_argument(
        "--target",
        choices=["bob", "claude-code", "cursor"],
        default="bob",
        help="Output target. Decides which configuration family Phase 2 will render. "
             "Default: bob.",
    )
    cp_parser.set_defaults(func=context_prompt_command)

    # 'generate' subcommand (Phase 2)
    gen_parser = subparsers.add_parser(
        "generate",
        help="Phase 2: consume the host agent's answer and write output files",
        description=(
            "Accepts a JSON blob via --context (inline) or --context-file (path). "
            "The blob contains partial_context (from Phase 1) plus bob_inference "
            "(the host agent's answers) and meta. Renders the Praxis output files "
            "into the appropriate per-target location under --output-root. Prints "
            "generated file paths to stdout, one per line."
        ),
    )
    # --context and --context-file are alternative ways to supply the same JSON
    # payload. Inline is convenient for short blobs and for the smoke test;
    # --context-file dodges shell quoting entirely (essential on Windows where
    # cmd / PowerShell mangle em-dashes, embedded double quotes, and CRLF
    # line endings inside a single-quoted JSON argument).
    context_group = gen_parser.add_mutually_exclusive_group(required=True)
    context_group.add_argument(
        "--context",
        type=str,
        help="Inline JSON blob with keys: partial_context, bob_inference, meta. "
             "Use --context-file instead when the blob contains characters that "
             "are awkward to quote in your shell (em-dashes, embedded double "
             "quotes, newlines).",
    )
    context_group.add_argument(
        "--context-file",
        type=str,
        help="Path to a UTF-8 JSON file containing the same blob structure as "
             "--context. Preferred over --context for non-trivial payloads, "
             "especially on Windows where cmd/PowerShell quoting is fragile.",
    )
    gen_parser.add_argument(
        "--output-root",
        type=str,
        required=True,
        help="Directory where praxis_output/ will be created",
    )
    gen_parser.set_defaults(func=generate_command)

    # Parse arguments and dispatch
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
