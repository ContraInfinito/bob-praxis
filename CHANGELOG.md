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
   - **Mitigation**: Dataclass is easy to extend; can add optional fields without breaking existing code
   - **Status**: Monitored

2. **Risk**: CLI might need additional global flags (--verbose, --output-dir)
   - **Mitigation**: Argparse supports global flags; can add before subparsers if needed
   - **Status**: Deferred to Phase 2+ based on user feedback

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