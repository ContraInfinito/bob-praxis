# Praxis

**AI-Powered Project Methodology Generator**

Praxis is a CLI tool that analyzes your project requirements and generates a comprehensive, actionable methodology document (PRAXIS_CONTRACT.md) tailored to your specific needs. It uses IBM watsonx.ai to understand your project context and recommend the best development approach, tech stack, and implementation strategy.

## What is Praxis?

Praxis bridges the gap between project ideas and structured execution plans. Instead of manually researching methodologies, frameworks, and best practices, Praxis:

- **Analyzes** your project requirements (from text input or markdown files)
- **Recommends** appropriate methodologies (Agile, Waterfall, hybrid approaches)
- **Suggests** optimal tech stacks based on your constraints
- **Generates** a complete PRAXIS_CONTRACT.md with phases, tasks, and success criteria
- **Provides** risk assessments and mitigation strategies

## Why Praxis Exists

Born during the IBM watsonx Challenge 2026 hackathon, Praxis solves a common problem: developers and teams often spend significant time deciding *how* to build something before they can start building. Praxis automates this decision-making process using AI, allowing you to:

- Start projects faster with clear direction
- Make informed methodology choices backed by AI analysis
- Reduce planning overhead and decision fatigue
- Get consistent, well-structured project plans

## Features

- **Two Input Modes**: Analyze existing markdown files or provide requirements via interactive prompts
- **AI-Powered Analysis**: Leverages IBM watsonx.ai (granite-3.1-8b-instruct) for intelligent recommendations
- **Comprehensive Output**: Generates detailed PRAXIS_CONTRACT.md with methodology, stack, phases, and risks
- **Flexible**: Works with any project type (web apps, APIs, data pipelines, etc.)
- **Secure**: Uses environment variables for API credentials (never commits secrets)

## Installation

### Prerequisites

- Python 3.8 or higher
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
   WATSONX_URL=https://us-south.ml.cloud.ibm.com
   ```

   **Important**: Never commit your `.env` file. It's already in `.gitignore`.

## Usage

Praxis supports two input modes: **analyze** (for existing markdown files) and **plan** (for interactive requirements gathering).

### Mode 1: Analyze Existing Requirements

If you already have a requirements document in markdown format:

```bash
python praxis.py analyze path/to/requirements.md
```

**Example**:
```bash
python praxis.py analyze docs/project_requirements.md
```

Praxis will:
1. Read and parse your markdown file
2. Send it to watsonx.ai for analysis
3. Generate `PRAXIS_CONTRACT.md` with recommended methodology and implementation plan

### Mode 2: Interactive Planning

If you want to describe your project interactively:

```bash
python praxis.py plan
```

Praxis will prompt you for:
- Project description
- Key requirements
- Constraints (timeline, budget, team size)
- Technical preferences

Then it generates the same comprehensive `PRAXIS_CONTRACT.md` output.

### Output

Both modes produce a `PRAXIS_CONTRACT.md` file containing:

- **Executive Summary**: Project overview and AI recommendations
- **Methodology Selection**: Chosen approach (Agile, Waterfall, etc.) with justification
- **Tech Stack Recommendations**: Languages, frameworks, tools, and why they fit
- **Implementation Phases**: Detailed breakdown of development stages
- **Risk Assessment**: Potential challenges and mitigation strategies
- **Success Criteria**: Measurable goals and KPIs

## Example Workflow

```bash
# 1. Activate virtual environment
venv\Scripts\activate

# 2. Run Praxis in plan mode
python praxis.py plan

# 3. Answer prompts about your project
# Project description: A real-time chat application for remote teams
# Key requirements: WebSocket support, user authentication, message history
# Constraints: 3-month timeline, team of 2 developers
# Tech preferences: Python backend, React frontend

# 4. Review generated PRAXIS_CONTRACT.md
# 5. Use it as your project roadmap
```

## Project Structure

```
bob-praxis/
├── praxis.py              # Main CLI entry point (to be implemented)
├── requirements.txt       # Python dependencies
├── .env                   # API credentials (not tracked)
├── .gitignore            # Git exclusions
├── LICENSE               # MIT License
├── README.md             # This file
├── CHANGELOG.md          # Version history
├── BOBCOIN_LOG.md        # Hackathon token usage tracking
├── test_watsonx.py       # API connection test script
└── bob_sessions/         # Development session exports
    └── README.md         # Session documentation
```

## Development Status

**Current Phase**: Phase 0 - Project Initialization (Complete)

Praxis is being developed as part of the IBM watsonx Challenge 2026 hackathon. The project follows a phased approach:

- **Phase 0**: ✅ Project setup, security baseline, documentation
- **Phase 1**: 🔄 Core CLI implementation (analyze mode)
- **Phase 2**: ⏳ Interactive plan mode
- **Phase 3**: ⏳ Output generation and formatting
- **Phase 4**: ⏳ Testing and refinement

See `CHANGELOG.md` for detailed progress updates.

## Contributing

This project is currently in active hackathon development. Contributions, issues, and feature requests are welcome after the initial release.

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Mathew Carballo López

## Acknowledgments

- Built for the IBM watsonx Challenge 2026 hackathon
- Powered by IBM watsonx.ai (granite-3.1-8b-instruct model)
- Developed with assistance from Cline (AI coding assistant)

## Contact

- GitHub: [@ContraInfinito](https://github.com/ContraInfinito)
- Repository: [bob-praxis](https://github.com/ContraInfinito/bob-praxis)

---

**Note**: This is a hackathon project under active development. Features and documentation are evolving rapidly.