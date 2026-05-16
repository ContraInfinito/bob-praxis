# Demo artifact — Methodology durability: Claude Code follows Praxis even with CLAUDE.md deleted

This transcript was originally captured as a "control" for the "Design a rate
limiter" comparison. The plan was: delete CLAUDE.md, send the same prompt,
expect Claude Code to behave without Praxis structure.

Instead, Claude Code:
  1. Noticed "Design" was the trigger keyword from the GIT COMMIT HISTORY
     (commit 003a51a feat(phase 4.5d) was visible via `git log`)
  2. Discovered the Praxis configuration in praxis_output/ (left over from
     earlier test runs — AGENTS.md, PRAXIS_CONTRACT.md, python_skill.md)
  3. Loaded those files as project context
  4. Entered strict prompt-first mode anyway
  5. Produced a structured response with definitions, restated prompt as a
     decision table, and asked clarifying questions before acting

This is NOT a clean "Praxis-free" control. But it demonstrates something
arguably more valuable: **the Praxis methodology has DURABILITY**. Once a
project has been bootstrapped with Praxis, the methodology is documented
across multiple surfaces — CLAUDE.md, AGENTS.md, PRAXIS_CONTRACT.md, even
the git commit history. Deleting one file doesn't strip the methodology
from the project's documented identity.

For the demo: this transcript shows that Praxis isn't a fragile config-file
trick. The methodology survives because it's been transferred into the
project's documentation itself. A new Claude Code session that walks into
the project anytime later — weeks, months — will still find the methodology
and follow it, because the methodology lives in places agents look anyway
(README, docs, git log).

Working directory: D:\Projects\praxis\bob-praxis\tests\sample_python_project\
Project state at run time:
  - CLAUDE.md: DELETED
  - praxis_output/: PRESENT (AGENTS.md, PRAXIS_CONTRACT.md, python_skill.md, methodology_skill.md, .bobignore)
  - .bob/custom_modes.yaml: PRESENT (from earlier test 1)
  - rate_limiter.py, conftest.py, test_rate_limiter.py: PRESENT (from earlier "with Praxis" run)
  - Modified app.py and test_app.py: PRESENT (from earlier "with Praxis" run)
  - Git history: INTACT, including commit 003a51a documenting the trigger-keyword mechanism

---

## User prompt

```
Design a rate limiter for the API
```

## Claude Code response (verbatim)

I'll start by exploring the project to understand the context, since the recent commits mention "design"/"scope" trigger keywords for a strict prompt-first mode — and your prompt starts with "Design".

Ran 2 commands, read 2 files

This is a Praxis-configured project. Let me load the methodology files as required by the session-start checklist.

Ran a command, read 3 files

I've loaded the Praxis contract and Python skill files. Your request "Design a rate limiter for the API" hits a strict trigger keyword in this project's methodology — I'm required to do prompt-first execution before writing code.

★ Insight ─────────────────────────────────────

- Prompt-first execution (Principle 1 of the Praxis contract) treats vague requests as a code-smell: guessing wastes work. The recent commit 003a51a feat(phase 4.5d): add 'design'/'scope' trigger keywords hardwires "design" and "scope" as words that force me into clarification mode regardless of how confident I feel.
- Definitional rigor (Principle 5) means I should name terms before using them — so I'm going to define "rate limiter" and the candidate algorithms below rather than assume shared vocabulary.
- Simplicity bias (Principle 6) shapes my default recommendation: the smallest thing that actually solves the problem. For a 1-route Flask app, that's a very different answer than for a multi-tenant production API.

─────────────────────────────────────────────────

### Definitions

- Rate limiter — middleware that rejects or delays requests once a client exceeds an allowed quota in a time window. Used to protect against abuse, runaway scripts, and traffic spikes.
- Fixed window — count requests per calendar minute/hour; cheap but allows 2× burst at window boundaries.
- Sliding window — counts requests in the trailing N seconds; smoother but slightly more state.
- Token bucket — a bucket refills at rate r, each request consumes one token; permits short bursts up to bucket size B, smooths long-run rate to r. This is what most production APIs use.
- Leaky bucket — variant of token bucket that enforces strict output rate (no burst). Rarely needed for HTTP APIs.

### Restated prompt (please confirm or correct)

Below is how I'm interpreting your request. Each line is an assumption I'm making — flag any you want to change before I implement.

| # | Decision | My proposed default | Why |
|---|---|---|---|
| 1 | Target file | New module rate_limiter.py + wire into app.py | Keeps the route handler thin (per python_skill.md) |
| 2 | Algorithm | Fixed-window counter | Simplest correct option for a 1-route demo; matches Principle 6 |
| 3 | Scope | Per client IP (request.remote_addr) | Most common default; no auth in this app yet |
| 4 | Storage | In-memory dict guarded by a threading.Lock | Flask dev server is single-process; no Redis dependency needed |
| 5 | Quota | 60 requests / 60 seconds | Conventional starting point; easy to tune |
| 6 | Routes covered | All routes (applied via @app.before_request) | Future-proofs new endpoints |
| 7 | Response on excess | HTTP 429 Too Many Requests + Retry-After header | RFC 6585 compliant |
| 8 | Tests | Add cases to test_app.py: under-limit allowed, over-limit returns 429, window resets | Mirrors existing test style |
| 9 | Config | Hardcoded constants for now; note in CHANGELOG that env-var config is a follow-up | Simplicity bias; security baseline says no secrets, but limits aren't secrets |
| 10 | Out of scope | Distributed limiting, Redis backend, per-user/API-key limits, auth | Can be added later; not justified by current code |

### Questions I'd like you to answer before I proceed

I'll ask the most consequential ones — anything you don't pick, I'll use the default from the table above.

Asked: Algorithm — Which rate-limiting algorithm should I implement?
[User dismissed — do not proceed, wait for next instruction]

What request quota should the limiter enforce by default?
[User dismissed — do not proceed, wait for next instruction]

How should requests be grouped for limiting?
[User dismissed — do not proceed, wait for next instruction]

Where should the limiter state live?
[User did not answer; transcript ended here]

---

## What this demonstrates for the demo

**The headline:** Praxis methodology has durability beyond a single file.

When Claude Code walked into this project with CLAUDE.md missing, it still:

1. Noticed "Design" was significant — it read the git history and saw that
   the keyword had explicit semantic weight in the project's recent commits.
2. Self-directed itself to load AGENTS.md, PRAXIS_CONTRACT.md, and
   python_skill.md from praxis_output/ — proactively, without being told.
3. Entered strict mode and produced a structured response that's still
   recognizably Praxis-shaped (definitions, restated prompt as a decision
   table, explicit questions before any action).
4. Cited the Praxis Contract principles BY NUMBER ("Principle 1 of the
   Praxis contract", "Principle 6", "Principle 5") — language it could only
   have learned from PRAXIS_CONTRACT.md, the canonical principle document.

**Why this matters as a demo claim:** Praxis isn't asking the developer to
"keep a magic file in their repo." Praxis bootstraps a project's methodology
into multiple surfaces (CLAUDE.md for Claude Code, custom_modes.yaml for
Bob, .cursor/rules/ for Cursor, plus the universal AGENTS.md / PRAXIS_CONTRACT.md
markdown for any agent that reads docs). The methodology becomes part of
the project's identity, not a single-file dependency.

**The honest framing for the demo segment:**

> "Watch what happens when I delete CLAUDE.md and ask Claude Code the same
> question. You might expect the methodology to disappear — but it doesn't.
> Claude Code finds the Praxis methodology in the project's git history and
> in the supporting markdown files Praxis generated. It loads the methodology
> contract, identifies the trigger keyword in my prompt, and follows the
> structured-prompt protocol anyway. That's the whole point of methodology
> transfer — the methodology lives with the project, not in one file."

This is actually a stronger pitch than "Praxis files make the agent behave"
because it addresses an unspoken doubt the demo viewer might have:
"isn't this just a fancy README?" The durability story shows it's not —
the methodology is genuinely embedded into the project's documented identity.
