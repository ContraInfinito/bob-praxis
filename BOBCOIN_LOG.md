# Bobcoin Consumption Log

Tracks IBM Bob Bobcoin consumption per phase. Bobcoins are the IBM Bob hackathon's session-reasoning currency. Each user gets 40 Bobcoins total for the hackathon.

All numbers below are read from Bob IDE's per-task consumption summary panel. Per-task figures are exact (as Bob reports them); phase totals are sums of per-task amounts where individual task numbers were captured, or approximations where multiple small tasks rolled together in a single Bob session.

## Budget

- **Total**: 40 Bobcoins
- **Demo reserve**: 15 Bobcoins (held back for Phase 5 demo runs)
- **Dev budget**: 25 Bobcoins (Phases 0–4 implementation)

## Phase Tracking

| Phase | Description | Estimate | Actual | Cumulative | Remaining | Notes |
|-------|-------------|----------|--------|------------|-----------|-------|
| Bootstrap | Brief restatement, risk analysis, Phase 0 planning | — | 0.29 | 0.29 | 39.71 | Pre-Phase-0 reasoning |
| Phase 0 | Project initialization and security baseline | 2.0 | 1.10 | 1.39 | 38.61 | LICENSE, README, .gitignore, requirements.txt, BOBCOIN_LOG, CHANGELOG, bob_sessions/ |
| Phase 1 | CLI skeleton + Python stack support | 6–10 | 6.48 | 7.87 | 32.13 | praxis package, detect.py, methodology.py, generate.py, 6 templates, sample Python project. Per-task figures in `bob_sessions/bob_task_may-15-2026_*.md`. |
| Phase 2 | Planning-doc mode, sample doc, ship-gate | 5–8 | ~11.5 | ~19.4 | ~20.6 | Sub-Task 1 (planning-doc parser ~2), Sub-Task 2 (CLI wiring + generate.py unification ~3), polish/sanitizer pass (~5), Sub-Task 3 (sample doc + ship-gate ~1.5). Spent over estimate; remaining-phase scope tightened in response. |
| Phase 3 | Praxis Bob custom mode | 3–5 | 0 | ~19.4 | ~20.6 | All work done via Claude Code + manual edits (deliberate Bobcoin conservation). Result: `.bob/custom_modes.yaml`, custom-mode wrapper, no Bob spend. |
| Phase 4 | Architecture refactor: two-phase handshake, multi-target dispatch (Bob / Claude Code / Cursor), trigger keywords, plan-mode clarifying questions, Windows-safe `--context-file` | 4–6 | ~4.0 | ~23.4 | ~16.6 | Multi-target template families, dispatch logic, trigger-keyword strict mode, plan-mode question generation. Live verification across all 6 mode×target combinations captured in `bob_sessions/bob_task_may-16-2026_*.md`. |
| Phase 5 | PyPI publication, auto-install Bob mode, demo, slides, submission | 1–2 (Bob) + demo reserve | ~0.4 | **23.78** | **16.22** | Phase 5A (PyPI publish): 0 Bobcoin (manual + Claude Code). Phase 5B (auto-install): minimal Bob involvement. Live demo recording: 0.25 Bobcoin (the Apply Praxis run captured on video). Slides/video/README polish: 0 Bobcoin (manual + Claude Code). |

**Final state (May 17, 2026, submission):** 23.78 Bobcoins spent of 40 total. 16.22 remaining. Demo reserve never needed to be deeply drawn down because the live demo run cost 0.25 Bobcoin and most polish work was done via Claude Code (no Bobcoin cost).

## Why some numbers are approximate

Bob's IDE shows exact per-task Bobcoin cost in the consumption summary, but during early phases (especially Phase 2) several small adjustments rolled into single Bob sessions without per-adjustment screenshots being captured. The exact final cumulative — **23.78 Bobcoins** — was read from Bob's running total, which is authoritative; the per-phase breakdown approximates that total based on session-level notes captured during development.

## Burn-rate observations

- **Phase 1** came in at the low end of its estimate (6.48 vs. 6–10 estimated).
- **Phase 2** ran significantly over (11.5 vs. 5–8 estimated). Two causes:
    1. Multiple Granite JSON-parsing retries (Granite was the original watsonx-based planning interpreter; this dependency was later removed entirely in Phase 4.1).
    2. A polish pass added prompt-sanitizer work mid-phase that wasn't in the original scope.
- **Phase 3** was free in Bobcoin terms by deliberately routing the work through Claude Code instead of Bob.
- **Phase 4** came in inside its estimate despite being the largest single architectural change in the project (full multi-target rewrite, two-phase handshake).
- **Phase 5** was nearly free because the heavy work was packaging, recording, and writing — none of which benefits from Bob's reasoning loop.

The conservation pattern (route mechanical work through Claude Code, reserve Bob for the high-context architectural decisions) is what kept the project well inside budget.

## Architectural note on the demo reserve

The 15-Bobcoin "demo reserve" was set up under the assumption that the recorded demo would involve heavy Bob interaction (multiple takes, scripted prompts). In practice the final recording is a single take of one Bob invocation (the zero-setup install), which cost 0.25 Bobcoin. The reserve was never substantially used.

---

**Last updated:** Phase 5 complete — May 17, 2026.
