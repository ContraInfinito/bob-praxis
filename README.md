# Praxis

**A methodology transfer tool for IBM Bob IDE.**

Praxis takes a developer's AI-collaboration methodology — their opinions about how an AI partner should work alongside them — and projects it onto any given codebase or planning document, producing tailored Bob IDE configuration that makes Bob behave consistently with that methodology on the specific project.

The name Praxis is Greek for "the practical application of theory." Praxis turns methodology theory (how I want to work with AI) into concrete Bob configuration (skills, custom modes, project rules) applied to a specific project (Python codebase, Unity project, planning doc).

## What Praxis Generates

Given either a project directory or a planning document, Praxis produces a tailored set of Bob configuration files:

- `AGENTS.md` — entry-point context document Bob reads on session start
- `PRAXIS_CONTRACT.md` — top-level AI-collaboration contract: how Bob will work with the developer on this specific project
- Stack-specific skill file (e.g., `python_skill.md`, `unity_skill.md`) — conventions, dependency awareness, common patterns for the detected stack
- Methodology skill file — the developer's transferable working-style opinions encoded as Bob behavior
- `.bobignore` — files Bob should never read or modify
- A custom Bob mode tailored to this project

## Architecture

Praxis is a hybrid of two interfaces backed by one engine:

1. **CLI core (Python)** — `praxis analyze ./project` or `praxis plan ./spec.md`. Deterministic. Detects stack, parses dependencies, assembles templates, writes output files. Calls watsonx.ai Granite for inference-heavy steps (planning-doc interpretation, stack-tailored prose generation).
2. **Praxis custom mode (markdown)** — wraps the CLI from inside Bob IDE. Adds conversational refinement and ambiguity handling.

The CLI is fully functional standalone. The custom mode is the enhanced experience.

## Default Methodology Principles

Praxis ships with seven hardcoded methodology defaults that users can override by editing the generated output files:

1. **Prompt-first execution** — rewrite vague user input into a structured prompt before acting
2. **Proactive issue resolution** — fix adjacent issues you spot, log what was done
3. **Code review by a second agent** — every change critiqued before presentation
4. **Logging discipline** — every session produces a changelog entry
5. **Definitional rigor** — define every technical term before using it
6. **Simplicity bias** — simplest solution that fully solves the problem
7. **Security baseline** — never plaintext credentials, scan for secrets, honor .bobignore

## Supported Stacks (v1)

- **Python** — requirements.txt and pyproject.toml; detects Flask, FastAPI, Django, pandas/numpy, pytest
- **Unity** — tool scripts vs game scripts, ScriptableObjects, Editor folder rules, Assembly Definition awareness
- **Generic fallback** for everything else

## Installation

### Prerequisites

- Python 3.11 or higher
- IBM watsonx.ai API credentials (API key and Project ID)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ContraInfinito/bob-praxis.git
   cd bob-praxis
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```env
   WATSONX_API_KEY=your_api_key_here
   WATSONX_PROJECT_ID=your_project_id_here
   WATSONX_ENDPOINT_URL=https://us-south.ml.cloud.ibm.com
   ```

   **Important**: Never commit your `.env` file. It's already in `.gitignore`.

## Usage

```bash
# Analyze an existing project
python -m praxis analyze ./my-project

# Bootstrap from a planning document
python -m praxis plan ./project_spec.md
```

Output appears in `<target>/praxis_output/`.

## Project Structure

```
bob-praxis/
├── praxis/                # Main Python package (Phase 1+)
│   ├── __init__.py
│   ├── __main__.py        # Entry point for python -m praxis
│   ├── cli.py             # Argparse CLI
│   ├── detect.py          # Stack detection
│   ├── methodology.py     # Hardcoded methodology defaults
│   ├── granite.py         # watsonx.ai integration
│   ├── generate.py        # Template assembly
│   └── templates/         # Output file templates
├── tests/                 # Sample projects for testing
├── bob_sessions/          # Exported Bob task sessions (submission requirement)
├── requirements.txt
├── .env                   # API credentials (not tracked)
├── .gitignore
├── LICENSE
├── README.md
├── CHANGELOG.md
├── BOBCOIN_LOG.md         # Bobcoin consumption tracking
└── test_watsonx.py        # watsonx.ai connectivity smoke test
```

## Status

Built for the IBM Bob Hackathon, May 15-17, 2026. See CHANGELOG.md for phase-by-phase progress.

- **Phase 0**: ✅ Project setup, security baseline, documentation
- **Phase 1**: 🔄 CLI skeleton + Python stack support
- **Phase 2**: ⏳ Planning-doc mode + Unity stack
- **Phase 3**: ⏳ Bob custom mode wrapper
- **Phase 4**: ⏳ Demo, docs, submission

## Acknowledgments

Built for the IBM Bob Hackathon 2026. Developed using IBM Bob IDE (https://bob.ibm.com) and IBM watsonx.ai Granite models. Reviewed and refined with Claude (Anthropic) as a second-agent reviewer.

## Contact

- GitHub: [@ContraInfinito](https://github.com/ContraInfinito)
- Repository: [bob-praxis](https://github.com/ContraInfinito/bob-praxis)

## License

MIT — see [LICENSE](LICENSE) file. Copyright (c) 2026 Mathew Carballo López.