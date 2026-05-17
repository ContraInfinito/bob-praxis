# Praxis

**Every time you switch AI coding assistants, you re-teach it your conventions. Praxis stops that.**

Praxis is a methodology transfer tool. It takes how you want an AI partner to work — the principles, the conventions, the moments when you want it to stop and ask — and projects them onto any project as configuration files that three different AI agents understand: **Bob IDE**, **Claude Code**, and **Cursor**.

Same methodology. Three idiomatic outputs. Loadable on day one without any manual import step.

The name *Praxis* is Greek for "the practical application of theory." It turns methodology theory (how I want to work with AI) into concrete configuration (rules, contracts, conventions) applied to a specific project.

---

## What Praxis Does

Given either an existing codebase or a planning document, Praxis generates the configuration files each agent expects, in the format that agent expects, in the location that agent automatically loads.

### For Bob IDE

A loadable project-scoped Bob mode plus supporting documentation:

- `.bob/custom_modes.yaml` — auto-discovered by Bob when the project is opened. The mode encodes the methodology, the trigger keywords, and the session-start checklist.
- `praxis_output/AGENTS.md` — project context, the seven methodology principles, and an "Open Questions for the Developer" section when generated from a planning document.
- `praxis_output/PRAXIS_CONTRACT.md` — the methodology contract in full form, including the strict-mode rider on Principle 1.
- `praxis_output/python_skill.md` — stack-specific conventions (Flask, FastAPI, Django, pytest, pandas/numpy patterns).
- `praxis_output/methodology_skill.md` — the seven principles as an enforcement guide.
- `praxis_output/.bobignore` — files Bob should never read or modify.

### For Claude Code

A single `CLAUDE.md` at the project root. Auto-loaded by Claude Code on session start. Contains the seven principles, the trigger-keyword section, project conventions, and the "Open Questions" list when generated from a planning document.

### For Cursor

Two `.mdc` files under `.cursor/rules/`. Auto-discovered when the project is opened in Cursor:

- `methodology.mdc` — project context and methodology principles, applied project-wide (`alwaysApply: true`).
- `python.mdc` — Python-language conventions, attached when editing `.py` files (`globs: "**/*.py"`).

### Target selection

The default target is Bob. To select a different target, the user includes a phrase in their natural-language invocation:

- `Apply Praxis to ./my-project` → Bob (default)
- `Apply Praxis to ./my-project for Claude Code` → Claude Code
- `Apply Praxis to ./my-project as CLAUDE.md` → Claude Code (alternative phrasing)
- `Apply Praxis to ./my-project for Cursor` → Cursor
- `Apply Praxis to ./my-project target Cursor` → Cursor (alternative phrasing)

The chosen target is announced in the first line of the response so the developer can catch a misinterpretation before any file is written.

---

## The Seven Methodology Principles

Praxis ships with seven hardcoded methodology defaults. Developers can override them by editing the generated configuration files.

1. **Prompt-first execution** — Rewrite vague user input into structured prompts before acting. *Strict mode (triggered by the keywords `design` or `scope`):* produce a six-field structured prompt and wait for explicit approval before any action, even if the request seems clear.
2. **Proactive issue resolution** — Fix adjacent issues you spot; log what was done.
3. **Code review by a second agent** — Every change critiqued before presentation.
4. **Logging discipline** — Every session produces a timestamped changelog entry.
5. **Definitional rigor** — Define every technical term before using it.
6. **Simplicity bias** — Simplest solution that fully solves the problem.
7. **Security baseline** — Never plaintext credentials; scan for secrets; honor `.bobignore`.

### Trigger keywords

When a user's message contains the keyword `design` or `scope` (case-insensitive, anywhere in the message), the agent enters strict prompt-first mode and produces a six-field structured prompt before any action:

1. **Restated request** — bullet-point reformulation of what the agent thinks the user wants
2. **Assumptions** — every assumption the agent would make if it proceeded as-is
3. **Scope IN** — what is included in the work
4. **Scope OUT** — what is deliberately excluded
5. **Proposed approach** — one or two sentences summarizing the implementation strategy
6. **Open questions** — anything the agent needs clarified before starting

The agent then waits for the developer to approve, edit, or reject the structured prompt. No code changes, file writes, or commands execute until approval.

This trigger surfaces redundantly across each agent's config: a dedicated top-of-file `Trigger Keywords` section AND a strict-mode rider embedded inside Principle 1's full description. Even if an agent skims past one, the other catches the trigger.

---

## Plan mode: surface what the planning doc didn't say

When given a planning document (`.md`, `.markdown`, or `.txt`) instead of an existing codebase, Praxis runs in **plan mode**. Plan mode generates the same per-target configuration, plus a list of clarifying questions about gaps in the planning document.

The questions land in two places:

- In the agent's chat response immediately, so the developer can answer them in conversation.
- Verbatim in the generated configuration's "Open Questions for the Developer" section, so future sessions (or future agents loading the project) see them too.

This is the architectural enforcement of Principle 1: the methodology doesn't trust the agent to remember to ask. It bakes the asking into the project's documentation.

---

## Two-phase handshake architecture

Praxis is a CLI that runs in two phases. The host agent (Bob, or any compatible orchestrator) bridges them.

**Phase 1: `praxis context-prompt <mode> <path> --target <target>`**

- Reads project files (analyze mode) or the planning document (plan mode).
- Detects stack and frameworks deterministically (no LLM call here).
- Builds a natural-language prompt for the host agent to answer.
- Emits JSON to stdout containing `prompt_for_bob`, `partial_context` (deterministic fields), and `meta`.

**Phase 2: `praxis generate --context-file <path> --output-root <dir>`**

- Reads the host agent's JSON answer plus the Phase 1 context from a file.
- Validates the schema.
- Renders the per-target templates.
- Writes files to the appropriate per-target locations.
- Prints generated file paths to stdout.

The `--context-file` flag avoids shell-quoting fragility on Windows (em-dashes, embedded quotes, newlines in JSON content all survive cleanly). An inline `--context '<json>'` flag is also accepted for trivially small payloads.

Both phases print machine-parseable output to stdout and human-readable status to stderr — clean for piping, clean for orchestration.

---

## Installation

### Prerequisites

- Python 3.11 or higher
- Bob IDE (for the Bob-orchestrated workflow), Claude Code (to consume Claude Code targets), or Cursor (to consume Cursor targets)

**No external API credentials are required.** Praxis has zero runtime dependencies as of v0.1.0. The host agent supplies the inference; Praxis only writes files.

### Quick install (recommended)

```bash
pip install praxis-bob
```

This installs the `praxis` command and the Python module (`python -m praxis`). No external API credentials required; Praxis has zero runtime dependencies.

### Zero-setup install (for Bob IDE users)

If you use [Bob IDE](https://bob.ibm.com), you can skip the `pip install` step entirely. Praxis ships as a Bob custom mode that auto-installs itself on first invocation:

1. Download `.bob/custom_modes.yaml` from this repository.
2. Import it into Bob: **Settings → Modes → Import / Create new mode**, pasting the YAML fields.
3. Activate the **🛠️ Praxis** mode and run a command like `Apply Praxis to ./my-project`.

On first invocation, the mode detects that Praxis isn't installed and runs `pip install --user praxis-bob` automatically. Subsequent invocations skip the check.

The auto-install path has the same end state as `pip install praxis-bob` — it just runs the command on your behalf. You can audit the install behavior by reading the mode's `customInstructions` field.

### Dev install (if you want to contribute or run the test suite)

```bash
git clone https://github.com/ContraInfinito/bob-praxis.git
cd bob-praxis
pip install -e ".[dev]"
python tests/test_two_phase_smoke.py
```

The `[dev]` extras install `pyyaml`, required only for the smoke test. Expected: all 7 paths and 2 mutex checks pass.

---

## Usage

### As a Bob custom mode (recommended)

Praxis ships as a project-scoped Bob mode in `.bob/custom_modes.yaml`. When you open this repository in Bob IDE, the **🛠️ Praxis** mode automatically appears in the mode list — no manual import needed.

1. Open this repository in Bob IDE.
2. Select **🛠️ Praxis** from Bob's mode selector.
3. Invoke with natural language:
   - **Apply to an existing codebase**: `Apply Praxis to ./tests/sample_python_project`
   - **Apply with a non-default target**: `Apply Praxis to ./tests/sample_python_project for Claude Code`
   - **Bootstrap from a planning document**: `Apply Praxis to ./tests/sample_planning_doc.md`

The Bob mode handles both phases of the CLI handshake transparently. It runs Phase 1, generates the inference internally, and invokes Phase 2 with `--context-file` (file-based handoff, safe across Windows/POSIX shells).

For planning-document input, Bob will surface any clarifying questions Praxis generated and wait for the developer to answer them before treating the configuration as final.

### As a standalone CLI

You can also drive Praxis directly without Bob, as long as you supply the inference yourself:

```bash
# Phase 1: read files, emit a prompt for the host agent
python -m praxis context-prompt analyze ./my-project --target bob > phase1.json

# Build a Phase 2 context blob: combine partial_context (from phase1.json),
# your bob_inference answer (the host agent's response), and meta into one JSON file.
# Write the combined blob to phase2.json.

# Phase 2: consume the combined blob, write output files
python -m praxis generate --context-file phase2.json --output-root ./my-project
```

The smoke test (`tests/test_two_phase_smoke.py`) is a working example of the standalone flow with a synthetic host-agent answer.

### As a global Bob meta-mode (apply to other projects on your machine)

To use Praxis on projects other than this repository:

1. Open Bob's Settings → Modes tab.
2. Click "Create new mode" (or equivalent).
3. Paste the YAML fields (`slug`, `name`, `roleDefinition`, `whenToUse`, `groups`, `customInstructions`) from this repo's `.bob/custom_modes.yaml` into the corresponding form fields.
4. Save.

The mode is now available in every project. Praxis's Python module (`python -m praxis`) must be importable in the target project's environment — clone this repo somewhere on `PYTHONPATH`, or add it to a project's virtualenv.

After Praxis runs against another project, its generated `.bob/custom_modes.yaml` is auto-discovered the next time that project opens in Bob. The Praxis meta-mode is a bootstrapper — once a project has its own generated mode, use that going forward.

---

## What's supported

- **Stack detection**: Python (Flask, FastAPI, Django, pandas, numpy, pytest)
- **Targets**: Bob IDE, Claude Code, Cursor
- **Modes**: `analyze` (existing codebase), `plan` (planning document)
- **Operating system**: developed and tested on Windows; Linux/macOS should work but are untested in v0.1.0
- **Generic fallback** for non-Python stacks returns a `NotImplementedError` in v0.1.0; multi-language support is deferred to v2

---

## Project structure

```
bob-praxis/
├── praxis/                       # Main Python package
│   ├── __init__.py
│   ├── __main__.py               # Entry point for `python -m praxis`
│   ├── cli.py                    # Argparse CLI (context-prompt + generate subcommands)
│   ├── detect.py                 # Stack and framework detection
│   ├── methodology.py            # The seven methodology principles
│   ├── inference_prompts.py      # Phase 1 prompt construction for the host agent
│   ├── generate.py               # Phase 2 template rendering and per-target dispatch
│   └── templates/                # Per-target template families
│       ├── bob/                  # AGENTS.md, PRAXIS_CONTRACT.md, custom_modes.yaml, etc.
│       ├── claude_code/          # CLAUDE.md
│       └── cursor/               # methodology.mdc, python.mdc
├── tests/
│   ├── test_two_phase_smoke.py   # End-to-end smoke test (7 paths + 2 mutex checks)
│   ├── sample_python_project/    # Test fixture for analyze mode
│   └── sample_planning_doc.md    # Test fixture for plan mode
├── bob_sessions/                 # Exported Bob sessions and demo transcripts
├── .bob/
│   └── custom_modes.yaml         # The Praxis Bob mode definition for this repository
├── requirements.txt              # pyyaml (smoke tests only)
├── .gitignore
├── LICENSE
├── README.md
├── CHANGELOG.md
└── BOBCOIN_LOG.md
```

---

## Verification

A two-phase smoke test exercises every (mode × target) combination plus both flag variants of the Phase 2 input:

```
python tests/test_two_phase_smoke.py
```

Coverage:

- 6 paths: {analyze, plan} × {bob, claude-code, cursor}
- 1 path: analyze + bob via `--context-file` (the Windows-safe alternative)
- 2 paths: argparse mutex checks rejecting both flags or neither

All 9 must pass for the build to be considered healthy.

---

## Status

Built for the IBM Bob Hackathon, May 15–17, 2026.

- **Phase 0**:  Project setup, security baseline, documentation
- **Phase 1**:  CLI skeleton + Python stack support
- **Phase 2**:  Planning-doc mode
- **Phase 3**:  Bob custom mode wrapper
- **Phase 4**:  Two-phase handshake, multi-target (Bob/Claude Code/Cursor), trigger keywords, plan-mode clarifying questions, Windows-safe Phase 2 via `--context-file`
- **Phase 5**:  Demo recording, slides, submission

See `CHANGELOG.md` for sub-task-level progress.

---

## Acknowledgments

Built for the IBM Bob Hackathon 2026.

- **Bob IDE** (https://bob.ibm.com) — the methodology's primary host agent and the CLI's first orchestrator.
- **Claude Code** and **Cursor** — the additional target ecosystems whose configurations Praxis generates.
- **Claude (Anthropic)** — second-agent reviewer during methodology and architecture design.

The seven methodology principles encoded in Praxis are derived from the author's working preferences with Claude over many months of collaborative development. Praxis is the act of writing those preferences down in a form other agents can read.

---

## Contact

- GitHub: [@ContraInfinito](https://github.com/ContraInfinito)
- Repository: [bob-praxis](https://github.com/ContraInfinito/bob-praxis)

---

## License

MIT — see [LICENSE](LICENSE) file. Copyright (c) 2026 Mathew Carballo López.
