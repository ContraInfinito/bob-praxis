# Demo artifact — Plan mode in Bob: Praxis surfaces clarifying questions

This transcript captures the demo's second-strongest moment: Praxis in PLAN
MODE, where Bob analyzes a planning document and produces a list of
clarifying questions that the developer must answer before implementation
begins. The questions land both in Bob's chat response AND verbatim in the
generated AGENTS.md file — making the methodology's "transfer authority
back to the developer" claim architectural, not just behavioral.

Captured during sub-task 4.6, test 4: bob target, plan mode against
tests/sample_planning_doc.md (a habit-tracker REST API planning doc).

Working directory: D:\Projects\praxis\bob-praxis\
Source document: tests/sample_planning_doc.md (habit-tracker API planning)
Bob mode active: 🛠️ Praxis (the root project's custom_modes.yaml)
Cost: 0.26 Bobcoin (clean, efficient Phase 2 invocation thanks to 4.5c
--context-file fix)

---

## User prompt

```
Apply Praxis to ./tests/sample_planning_doc.md
```

(No target keyword → defaults to bob. The path is a .md file → Pattern 2
of the Praxis Bob mode fires, switching to plan mode.)

## Bob response (verbatim)

Praxis successfully applied to the planning document at `./tests/sample_planning_doc.md`.

**Detected Configuration:**

- Stack: Python
- Frameworks: Flask, pytest
- Integrations: PostgreSQL, SendGrid, Sentry
- Target: bob

**Generated Files:**

- `tests/praxis_output/AGENTS.md` — Project context and session-start checklist
- `tests/praxis_output/PRAXIS_CONTRACT.md` — The 7 methodology principles
- `tests/praxis_output/python_skill.md` — Flask and pytest conventions
- `tests/praxis_output/methodology_skill.md` — Methodology enforcement rules
- `tests/praxis_output/.bobignore` — Files Bob should never touch
- `tests/.bob/custom_modes.yaml` — Loadable Bob mode definition

**5 Clarifying Questions Identified:**

The planning document left these gaps that need developer input before implementation:

1. How should timezone handling work for completion dates — store user timezone or accept client-provided dates?
2. What are the specific JWT token expiration policies for authentication?
3. What's the exact definition of 'custom frequency' for habits — any integer per week, or specific patterns?
4. Should the weekly digest email be opt-in or opt-out by default?
5. What are the rate limiting requirements for the API endpoints?

**Next Steps:**

The generated `tests/.bob/custom_modes.yaml` will be auto-discovered by Bob the next time you open this project. The project-specific mode `sample-planning-doc` is now loadable without any manual import. When you're ready to start implementing the Habit Tracker API, activate that mode and Bob will follow the methodology principles defined in the generated configuration.

---

## User response

```
noted as TODOs, proceed without answers
```

## Bob continuation (verbatim)

🎉 Task Completed

Praxis bootstrap complete for the Habit Tracker API project. The 5 clarifying questions are documented in `tests/praxis_output/AGENTS.md` as TODOs for future resolution.

The generated configuration is ready to use. The project-specific Bob mode `sample-planning-doc` will be auto-discovered next time you open this project in Bob IDE.

---

## On-disk verification

The clarifying questions landed verbatim in the generated AGENTS.md file
under a dedicated section. This is architectural — the questions are
preserved in the project's documentation, not just in the Bob chat
transcript. From `tests/praxis_output/AGENTS.md`:

```markdown
## Open Questions for the Developer

The planning document didn't specify these. Ask the developer at session start:

- How should timezone handling work for completion dates — store user timezone or accept client-provided dates?
- What are the specific JWT token expiration policies for authentication?
- What's the exact definition of 'custom frequency' for habits — any integer per week, or specific patterns?
- Should the weekly digest email be opt-in or opt-out by default?
- What are the rate limiting requirements for the API endpoints?
```

This means any future Bob session that loads AGENTS.md (per the Session
Start Checklist) will see these questions and surface them to the developer.
The methodology's "Prompt-first execution" is enforced at the documentation
layer, not just by the agent's behavior in the moment.

The Trigger Keywords section is also present in this generated AGENTS.md
(consistent with 4.5d), so the methodology survives across plan-mode
configurations too.

---

## Why this is demo gold

This single test captures three demo-relevant points in one interaction:

1. **Plan mode works.** Praxis can bootstrap a project that doesn't have
   code yet, just a planning document. This is a real product use case —
   developers often have a spec before they have a codebase.

2. **Bob's stack inference from prose is accurate.** The planning doc
   mentions Flask, pytest, PostgreSQL, SendGrid, and Sentry in different
   sections; Bob extracted all five correctly and stamped them into the
   generated configuration.

3. **The clarifying-questions moment is the demo's strongest single beat.**
   Five specific questions, each one a real scoping decision that the
   planning doc glossed over. Each one would otherwise be silently
   answered by whatever agent eventually starts the implementation.

The questions Bob surfaced are NOT generic ("what is the goal?", "who is
the user?"). They are technically specific: timezone storage policy, JWT
expiration, frequency semantics, email defaults, rate-limit requirements.
These are the kind of details a real product manager would have to clarify
before engineering starts. Praxis caught them automatically.

This is the demo segment that proves the central claim: "Praxis transfers
decision authority back to the developer when ambiguity surfaces." The
ambiguity is in the planning doc. Praxis enumerates it. The developer
chooses how to resolve it. The agent doesn't guess.

---

## Demo framing for Phase 5

Use this transcript as a 60-90 second segment in the demo video.

**Setup shot:** Show tests/sample_planning_doc.md briefly (the spec). Show
that there's no code yet, just the doc.

**Action shot:** In Bob, type `Apply Praxis to ./tests/sample_planning_doc.md`.

**Payoff shot:** Bob responds with five specific clarifying questions, says
it will wait, presents the questions in a numbered list. The viewer sees
the structured response form.

**Reveal shot:** Open the generated AGENTS.md. Scroll to "Open Questions
for the Developer." The same five questions are documented in the file.

**Narration:** "Praxis didn't just ask the questions — it baked them into
the project's documentation. Every future agent that loads this project
will see them. The methodology isn't a one-shot interaction; it becomes
part of the project's identity."

That's the segment.
