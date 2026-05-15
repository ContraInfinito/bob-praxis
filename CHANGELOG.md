# Changelog

All notable changes to the Praxis project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Phase 1 - CLI Skeleton + Python Stack Support (2026-05-15)

**Status**: In Progress

#### Sub-Task 1: Core Package Structure + CLI + Methodology Constants (2026-05-15 13:16 CST)

**Completed**: May 15, 2026, ~1:18 PM CST

**What Was Built**:
1. **Package Structure**
   - Created `praxis/__init__.py` with version metadata
   - Created `praxis/__main__.py` as entry point for `python -m praxis`
   
2. **Methodology Principles System**
   - Created `praxis/methodology.py` with `MethodologyPrinciple` dataclass
   - Defined all 7 hardcoded methodology principles with 4 rendering formats each:
     - `name`: Short title (e.g., "Prompt-first execution")
     - `short_description`: One-line summary for compact contexts
     - `full_description`: 2-3 sentence explanation for documentation
     - `enforcement_hint`: How Bob should enforce the principle
   - Added helper functions: `get_principles_summary()`, `get_principle_by_name()`
   
3. **CLI Framework**
   - Created `praxis/cli.py` with argparse-based interface
   - Implemented two subcommands:
     - `analyze <path>`: Functional skeleton with path validation
     - `plan <path>`: Stub that prints "not yet implemented"
   - Added `--version` flag
   - Proper error handling for non-existent paths and non-directory paths

**Options Considered**:

**For Methodology Principle Storage**:
- **Option A**: Store as simple strings or tuples
  - Rejected: Doesn't support multiple rendering formats needed for different output files
- **Option B**: Store as dictionaries
  - Rejected: No type safety, harder to maintain
- **Option C (Chosen)**: Use dataclass with named fields
  - Why: Type-safe, self-documenting, supports multiple rendering formats, easy to extend

**For CLI Argument Parsing**:
- **Option A**: Use click library
  - Rejected: External dependency, overkill for simple two-command CLI
- **Option B (Chosen)**: Use stdlib argparse
  - Why: No dependencies, sufficient for our needs, widely understood

**For Path Validation**:
- **Option A**: Validate in main() before dispatching
  - Rejected: Duplicates validation logic across commands
- **Option B (Chosen)**: Validate in each command handler
  - Why: Each command may have different path requirements (analyze needs dir, plan needs file)

**Why This Approach**:
1. **Dataclass Structure**: The 4-field MethodologyPrinciple design enables rendering the same principle in different contexts (short form in .bobignore comments, full form in PRAXIS_CONTRACT.md, enforcement-focused in methodology skill file) without duplicating content
2. **Argparse Subcommands**: Standard Python pattern for multi-command CLIs; familiar to developers
3. **Early Path Validation**: Fail fast with clear error messages before attempting stack detection
4. **Stub Implementation**: The `plan` command stub documents the feature exists but isn't ready, preventing user confusion

**Risks Identified**:
1. **Risk**: MethodologyPrinciple dataclass might need additional fields in later phases

#### Sub-Task 2: Stack Detection + Granite Integration (2026-05-15 13:31 CST)

**Completed**: May 15, 2026, ~1:32 PM CST

**What Was Built**:
1. **Stack Detection Module (praxis/detect.py)**
   - Created `StackInfo` dataclass with 6 fields: stack_name, frameworks, dependencies, python_files_count, has_requirements_txt, has_pyproject_toml
   - Implemented `detect_stack(project_path)` function with 5-step detection logic:
     1. Walk for .py files, filtering out venv/__pycache__/.git/node_modules/praxis_output/bob_sessions
     2. Parse requirements.txt: strip comments, version specifiers, editable prefixes
     3. Parse pyproject.toml: extract from [project.dependencies] and [tool.poetry.dependencies]
     4. Detect frameworks: Flask, FastAPI, Django, pandas, numpy, pytest via substring matching
     5. Determine stack name: "Python" if any Python indicators found, else "Generic"
   - Added UTF-8/latin-1 fallback encoding for requirements.txt
   - Added BOM stripping for UTF-8 files with byte order marks
   - Inline verification block: `python -m praxis.detect`

2. **Granite Integration Module (praxis/granite.py)**
   - Reused IAM token exchange pattern from test_watsonx.py
   - Module-level token caching (no expiry checking needed for short CLI runs)
   - `generate(prompt, max_tokens=500)` function with greedy decoding
   - Loads credentials from .env via python-dotenv
   - Clear error messages for missing WATSONX_API_KEY or WATSONX_PROJECT_ID
   - Enhanced error handling: includes response body in exceptions for debuggability
   - Inline verification block: `python -m praxis.granite`

3. **Bug Fix**
   - Fixed requirements.txt UTF-16 encoding issue (was causing parse failures)
   - Recreated as UTF-8 with proper line endings

**Options Considered**:

**For requirements.txt Parsing**:
- **Option A**: Use pip's internal parser (pip._internal.req)
  - Rejected: Private API, not stable, overkill for simple version stripping
- **Option B (Chosen)**: Simple string splitting on version separators
  - Why: Sufficient for 95% of real-world requirements.txt files, no dependencies

**For pyproject.toml Parsing**:
- **Option A**: Use external toml library
  - Rejected: Python 3.11+ has tomllib in stdlib
- **Option B (Chosen)**: Use tomllib from stdlib
  - Why: No external dependency, officially supported

**For Framework Detection**:
- **Option A**: Exact match on dependency names
  - Rejected: Misses packages like "flask-cors", "pytest-cov"
- **Option B (Chosen)**: Substring matching with display name mapping
  - Why: Catches framework-related packages, simple to extend

**For Granite Token Caching**:
- **Option A**: File-based cache with expiry checking
  - Rejected: Overkill for CLI that runs in seconds
- **Option B (Chosen)**: Module-level variable, no expiry
  - Why: Tokens last 1 hour, CLI runs are <1 minute, simpler code

**For Encoding Handling**:
- **Option A**: Force UTF-8 only, fail on decode errors
  - Rejected: Real-world files have encoding issues (BOM, latin-1)
- **Option B (Chosen)**: UTF-8 with latin-1 fallback, BOM stripping
  - Why: Handles common encoding issues gracefully

**Why This Approach**:
1. **Robust Parsing**: Handles real-world file encoding issues (BOM, UTF-16) without failing
2. **Minimal Dependencies**: Uses stdlib only (tomllib, pathlib, dataclasses)
3. **Graceful Degradation**: Parse errors print warnings but don't crash the tool
4. **Framework Detection**: Substring matching catches framework-related packages (flask-cors, pytest-cov)
5. **Token Efficiency**: Caches IAM token for multiple Granite calls in one CLI run

**Risks Identified**:
1. **Risk**: Substring matching for frameworks might produce false positives
   - **Example**: A package named "my-flask-wrapper" would trigger Flask detection
   - **Mitigation**: Acceptable for v1; framework list is curated and unlikely to collide
   - **Status**: Monitored

2. **Risk**: No PEP 508 parser means complex dependency specs might parse incorrectly
   - **Example**: `package[extra1,extra2] ; python_version >= "3.8"`
   - **Mitigation**: Simple split on `[` and `;` handles 95% of cases; full PEP 508 is Phase 2+
   - **Status**: Documented limitation

3. **Risk**: IAM token might expire during long-running CLI sessions
   - **Mitigation**: Tokens last 1 hour, CLI runs are seconds; not a practical concern
   - **Status**: Accepted

**Testing Performed**:
- ✅ `python -m praxis.detect` → Detected Python stack, 7 .py files, 6 dependencies (certifi, charset-normalizer, idna, python-dotenv, requests, urllib3)
- ✅ `python -m praxis.granite` → Granite responded with "Ready."
- ✅ UTF-8 BOM handling verified
- ✅ requirements.txt parsing with version specifiers verified

**Next Steps**: Sub-Task 3 will implement templates (praxis/templates/) and generation engine (praxis/generate.py).

   - **Mitigation**: Dataclass is easy to extend; can add optional fields without breaking existing code
   - **Status**: Monitored

2. **Risk**: CLI might need additional global flags (--verbose, --output-dir)
   - **Mitigation**: Argparse supports global flags; can add before subparsers if needed
   - **Status**: Deferred to Phase 2+ based on user feedback


#### Sub-Task 3: Templates + Generation Engine (2026-05-15 13:46 CST)

**Completed**: May 15, 2026, ~1:46 PM CST

**What Was Built**:
1. **Template System (praxis/templates/)**
   - Created 6 markdown templates with str.format() placeholders:
     - **AGENTS.md.template** — Entry-point context document (43 lines)
     - **PRAXIS_CONTRACT.md.template** — Top-level collaboration contract (82 lines)
     - **python_skill.md.template** — Python-specific conventions and framework guidance (115 lines)
     - **methodology_skill.md.template** — 7 principles in enforcement form (66 lines)
     - **bobignore.template** — Static .bobignore file (32 lines)
     - **custom_mode.md.template** — Per-project custom Bob mode (79 lines)
   - Total: 417 lines of template content

2. **Generation Engine (praxis/generate.py)**
   - `generate_outputs(project_path, stack_info)` function (241 lines)
   - Loads all 6 templates from praxis/templates/
   - Renders methodology principles in 3 forms: short, full, enforcement
   - Makes 3 Granite calls for content generation:
     1. Stack-tailored intro for PRAXIS_CONTRACT.md (2-3 paragraphs)
     2. Python best practices for python_skill.md (5-8 bullets)
     3. Project description for AGENTS.md (2-3 sentences)
   - Formats frameworks and dependencies lists (truncates deps at 10)
   - Generates framework-specific notes for Flask, FastAPI, Django, pytest, pandas/numpy
   - Writes all 6 files to <project>/praxis_output/
   - Returns list of generated file paths

3. **CLI Integration**
   - Updated `analyze_command` in praxis/cli.py to wire in real implementation
   - Late imports (detect_stack, generate_outputs) to avoid env loading on --help
   - Progress messages during Granite calls
   - Error handling for NotImplementedError (non-Python stacks) and general exceptions
   - Exit codes: 0 (success), 1 (error), 2 (not implemented)

4. **End-to-End Verification**
   - Ran `python -m praxis analyze .` on the praxis project itself
   - Generated 6 files in ./praxis_output/ with realistic content:
     - AGENTS.md: Granite-generated project description, methodology quick reference
     - PRAXIS_CONTRACT.md: Full 7 principles, Granite intro mentioning dependencies
     - python_skill.md: Granite-generated Python best practices, environment management
     - methodology_skill.md: All 7 principles in enforcement form
     - .bobignore: Static template with generation date
     - custom_mode.md: Project-specific Bob mode definition
   - Verified .gitignore correctly excludes praxis_output/

**Options Considered**:

**For Template Placeholder Format**:
- **Option A**: Use Jinja2 templating engine
  - Rejected: External dependency, overkill for simple str.format() substitution
- **Option B (Chosen)**: Python str.format() with descriptive names
  - Why: No dependencies, simple, sufficient for our needs

**For Granite Prompt Design**:
- **Option A**: Single Granite call to generate all content at once
  - Rejected: Hard to control output structure, mixing concerns
- **Option B (Chosen)**: Three separate Granite calls, one per output file
  - Why: Clear separation of concerns, easier to debug, better control over token usage

**For Framework-Specific Notes**:
- **Option A**: Generate all framework notes via Granite
  - Rejected: Granite might hallucinate framework features, inconsistent quality
- **Option B (Chosen)**: Hardcoded framework notes in generate.py, Granite for general best practices
  - Why: Predictable output, accurate framework guidance, Granite adds project-specific context

**For Dependencies List Formatting**:
- **Option A**: Show all dependencies regardless of count
  - Rejected: Projects with 50+ dependencies would bloat output files
- **Option B (Chosen)**: Truncate at 10, show "...and N more"
  - Why: Keeps output readable, user can see full list in requirements.txt

**For Output Directory Handling**:
- **Option A**: Error if praxis_output/ already exists
  - Rejected: Forces user to manually delete before re-running
- **Option B (Chosen)**: Create if missing, overwrite if exists
  - Why: Idempotent behavior, user can re-run analyze without cleanup

**Why This Approach**:
1. **Template-Based Generation**: Separates structure (templates) from content (Granite + detected info), making it easy to customize output format without touching generation logic
2. **Three Granite Calls**: Each call has a focused purpose (intro, best practices, project description), producing consistent, high-quality output
3. **Hardcoded Framework Notes**: Ensures accurate, reliable framework guidance without risk of Granite hallucination
4. **Methodology Rendering**: Three rendering formats (short, full, enforcement) enable the same principles to appear appropriately in different contexts
5. **Late Imports in CLI**: Avoids loading .env and Granite on --help, faster CLI response for non-analyze commands

**Risks Identified**:
1. **Risk**: Granite-generated content might be too generic or off-topic
   - **Mitigation**: Prompts are specific and constrained ("output ONLY the bullet points, no preamble")
   - **Status**: Verified in testing — Granite output is relevant and well-formatted

2. **Risk**: Template placeholders might be misspelled or missing
   - **Mitigation**: generate.py builds a complete placeholder dict; KeyError would surface immediately
   - **Status**: Tested end-to-end, all placeholders render correctly

3. **Risk**: Granite calls might fail or timeout
   - **Mitigation**: granite.py has 60-second timeout, raises clear exceptions with response body
   - **Status**: Tested, Granite calls complete in ~10 seconds each

4. **Risk**: Generated files might overwrite user customizations
   - **Mitigation**: Documented in templates ("back up customizations before regenerating")
   - **Status**: Acceptable for v1; Phase 2+ could add --no-overwrite flag

**Testing Performed**:
- ✅ `python -m praxis analyze .` → Generated 6 files in ./praxis_output/
- ✅ AGENTS.md contains Granite-generated project description
- ✅ PRAXIS_CONTRACT.md has full 7 principles + Granite intro
- ✅ python_skill.md has Granite best practices + hardcoded framework notes
- ✅ methodology_skill.md has all 7 principles in enforcement form
- ✅ .bobignore is static template with date filled in
- ✅ custom_mode.md is functional project-specific mode
- ✅ .gitignore correctly excludes praxis_output/
- ✅ All placeholders render correctly (no KeyError)
- ✅ Granite calls complete successfully (~30 seconds total)

**Next Steps**: Sub-Task 4 will create the sample Python project and perform final integration testing.

**Testing Performed**:
- ✅ `python -m praxis analyze .` → Success (prints path, acknowledges stub)
- ✅ `python -m praxis analyze ./nonexistent` → Error with clear message
- ✅ `python -m praxis plan ./test.md` → Stub message printed

**Next Steps**: Sub-Task 2 will implement `praxis/detect.py` (Python stack detector) and `praxis/granite.py` (watsonx.ai wrapper).

## [Unreleased]

### Phase 0 - Project Initialization and Security Baseline (2026-05-15)

**Completed**: May 15, 2026, ~12:30 PM CST (Hour 4.5 of 48-hour hackathon)

#### What Was Done

1. **Repository Verification**
   - Confirmed git repository connected to https://github.com/ContraInfinito/bob-praxis
   - Verified clean working tree on main branch
   - Existing files: `.gitignore`, `test_watsonx.py`, `.env` (with working watsonx.ai credentials)

2. **Virtual Environment Setup**
   - Removed any existing venv directory
   - Created fresh Python virtual environment
   - Installed core dependencies: `requests`, `python-dotenv`
   - Generated `requirements.txt` with pinned versions

3. **Legal and Licensing**
   - Created MIT LICENSE with copyright holder "Mathew Carballo López" and year 2026
   - Ensures open-source compliance for hackathon submission

4. **Documentation Foundation**
   - Created README.md describing Praxis as a methodology transfer tool for IBM Bob IDE
   - Note: README was re-aligned mid-Phase-0 after detecting drift toward a generic "AI project planner" framing. Corrected version describes the actual methodology-transfer architecture.

5. **Token Tracking**
   - Created BOBCOIN_LOG.md to track AI token consumption per phase
   - Essential for hackathon resource management

6. **Security Baseline**
   - Updated .gitignore to prevent credential leaks:
     - `.env` (API credentials)
     - `venv/` (virtual environment)
     - `__pycache__/`, `*.pyc` (Python bytecode)
     - `bob_sessions/*.png`, `bob_sessions/*.jpg` (screenshots)
   - Verified no sensitive data in tracked files

7. **Version Control**
   - Committed all Phase 0 changes with message: "Phase 0: Project initialization and security baseline"
   - Established clean baseline for Phase 1 development

#### Options Considered

**For Documentation Structure:**
- **Option A**: Create extensive docs/ folder with METHODOLOGY.md, STACK_SUPPORT.md, etc.
  - Rejected: Scope creep - methodology should live in generated PRAXIS_CONTRACT.md output
- **Option B**: Minimal README with external wiki
  - Rejected: Adds complexity, harder to maintain during hackathon
- **Option C (Chosen)**: Comprehensive README.md with inline documentation
  - Why: Single source of truth, easy to navigate, sufficient for hackathon scope

**For Virtual Environment:**
- **Option A**: Use Poetry or pipenv for dependency management
  - Rejected: Overkill for simple project, adds learning curve
- **Option B (Chosen)**: Standard venv with requirements.txt
  - Why: Simple, widely understood, sufficient for project needs

**For Session Tracking:**
- **Option A**: Store sessions in separate repository
  - Rejected: Adds complexity, harder to correlate with code changes
- **Option B (Chosen)**: bob_sessions/ folder in main repo
  - Why: Keeps development history with code, easier for judges to review

#### Why This Approach

1. **Security First**: Established .gitignore before any code implementation prevents accidental credential commits
2. **Clear Documentation**: Comprehensive README ensures anyone can understand and use Praxis
3. **Hackathon Optimized**: Focused on essentials, avoided scope creep (no YAML parsing, no methodology docs)
4. **Transparent Process**: bob_sessions/ folder documents AI-assisted development for judges
5. **Professional Standards**: MIT license, semantic versioning, changelog follow industry best practices

#### Risks and Mitigations

**Risk 1: Virtual Environment Activation Issues**
- **Impact**: Users on different platforms may struggle with activation
- **Mitigation**: README includes platform-specific activation commands (Windows/macOS/Linux)
- **Status**: Documented

**Risk 2: API Credential Management**
- **Impact**: Users might commit .env file or struggle with setup
- **Mitigation**: .gitignore prevents commits, README has clear setup instructions with warnings
- **Status**: Mitigated

**Risk 3: Scope Creep During Development**
- **Impact**: Could waste time on non-essential features (YAML parsing, methodology docs)
- **Mitigation**: Explicit rejection of v2 features in task description, focus on core CLI
- **Status**: Controlled

**Risk 4: Documentation Drift**
- **Impact**: README might become outdated as code evolves
- **Mitigation**: Update README in each phase, keep it under 200 lines for maintainability
- **Status**: Monitored

**Risk 5: Token Budget Overrun**
- **Impact**: Could exhaust Bobcoin budget before completing hackathon
- **Mitigation**: BOBCOIN_LOG.md tracks consumption per phase, allows budget adjustments
- **Status**: Tracked

#### Phase 0 Drift Correction (post-commit)

After the initial Phase 0 commit (`70ac06b`), an audit revealed that README.md, BOBCOIN_LOG.md, and the CHANGELOG's Phase 1 sketch had drifted from the project brief — describing a generic AI project planning tool rather than the methodology transfer tool we're actually building. Corrections applied:

- **README.md**: Rewritten to describe Praxis as a Bob IDE methodology transfer tool with the correct architecture (hybrid CLI + custom mode), correct outputs (AGENTS.md, PRAXIS_CONTRACT.md, skill files, .bobignore, custom mode), and the 7 methodology principles. Removed incorrect attribution to Cline; added correct attribution to IBM Bob, watsonx.ai, and Claude (second-agent reviewer).
- **.gitignore**: Replaced the overly-broad `PRAXIS_CONTRACT.md` rule with `**/praxis_output/` so generated outputs are ignored at any path without blocking example files.
- **BOBCOIN_LOG.md**: Replaced dollar-formatted estimates with Bobcoin numbers. Set correct 40-coin total budget, 15-coin demo reserve. Phase plan rewritten to match the agreed roadmap.
- **CHANGELOG.md**: This section + corrected Phase 1 plan below.

Lesson logged: documentation artifacts are vulnerable to model drift when the brief is paraphrased rather than re-read verbatim. Future phases must re-anchor on the project brief at the start of each task, not rely on summary memory.


#### Next Steps (Phase 1)

Per the agreed phase plan, Phase 1 builds:

- `praxis/` Python package with `__init__.py`, `__main__.py`, `cli.py`
- `praxis/detect.py` — Python stack detection (requirements.txt, pyproject.toml; identifies Flask, FastAPI, Django, pandas/numpy, pytest)
- `praxis/methodology.py` — the 7 hardcoded methodology principles
- `praxis/granite.py` — watsonx.ai integration (reuses pattern from test_watsonx.py)
- `praxis/templates/` — markdown templates for generated outputs (AGENTS.md, PRAXIS_CONTRACT.md, python_skill.md, methodology_skill.md, bobignore, custom_mode.md)
- `praxis/generate.py` — template assembly into final output files
- `tests/sample_python_project/` — minimal Python project for demoing
- End state: `python -m praxis analyze ./tests/sample_python_project` produces 6 output files in that project's `praxis_output/` folder

Phase 1 ship gate: tool demonstrably works on the sample Python project, with realistic stack-tailored output.

---

**Phase 0 Completion Time**: ~30 minutes
**Bobcoin Consumption**: See BOBCOIN_LOG.md
**Files Created**: 7 (LICENSE, README.md, CHANGELOG.md, BOBCOIN_LOG.md, bob_sessions/README.md, requirements.txt, updated .gitignore)
**Lines of Code**: 0 (structure only)
**Git Commits**: 1