# Bobcoin Consumption Log

Tracks Bob IDE Bobcoin consumption per phase. Bobcoins are the IBM Bob hackathon's session-reasoning currency. Each user gets 40 Bobcoins total; once exhausted, no more Bobcoins are issued for the hackathon.

## Budget

- **Total**: 40 Bobcoins
- **Demo reserve**: 15 Bobcoins (Phase 4 demo runs)
- **Dev budget**: 25 Bobcoins (Phases 0-3 reasoning)

## Phase Tracking

| Phase | Description | Estimated | Actual | Cumulative | Remaining | Notes |
|-------|-------------|-----------|--------|------------|-----------|-------|
| Bootstrap | Brief restatement, risk analysis, Phase 0 planning | - | 0.29 | 0.29 | 39.71 | Pre-Phase-0 reasoning |
| Phase 0 | Project initialization and security baseline | 2.0 | 1.10 | 1.39 | 38.61 | File creation, README, LICENSE, gitignore, requirements.txt, bob_sessions setup |
| Phase 1 | CLI skeleton + Python stack support | 6-10 | TBD | TBD | TBD | praxis package, detect.py, granite.py, generate.py, templates, sample Python project |
| Phase 2 | Planning-doc mode + Unity stack | 5-8 | TBD | TBD | TBD | praxis plan command, Unity detector, Granite-based planning-doc interpretation |
| Phase 3 | Bob custom mode wrapper | 3-5 | TBD | TBD | TBD | Custom mode .md file, CLI integration via Bob |
| Phase 4 | Demo, docs, submission | 1-2 (Bob) + 15 (demo) | TBD | TBD | TBD | README polish, demo video, submission upload |

## Update Procedure

After each phase ends:
1. Take screenshot of Bob task consumption summary
2. Save screenshot to `bob_sessions/phase<N>_completion_summary.png`
3. Update the table row above with actual Bobcoin number
4. Recompute cumulative and remaining
5. If actual significantly exceeds estimate, re-evaluate remaining-phase scope

## Risk Threshold

If cumulative consumption reaches 25 Bobcoins before Phase 4 starts, we have crossed into the demo reserve. At that point, immediately cut scope to demo-critical features only.

---

**Last Updated**: Phase 0 complete — May 15, 2026