# Demo artifact — Clean Praxis-naive baseline ("Design a rate limiter")

This is the third leg of a three-way comparison demonstrating how Praxis
methodology affects Claude Code's behavior on the same prompt.

This transcript captures Claude Code's behavior on a project that has NEVER
seen Praxis: a fresh copy of just app.py, requirements.txt, and test_app.py
placed in a new directory outside the bob-praxis repository. No CLAUDE.md,
no AGENTS.md, no praxis_output/, no .bob/, no git history that mentions
Praxis or trigger keywords. A truly Praxis-naive baseline.

Working directory: D:\Projects\praxis_demo_baseline\
Project state:
  - app.py — canonical hello-world Flask app (copied from bob-praxis)
  - test_app.py — single pytest test for the hello route (copied)
  - requirements.txt — flask==3.0.0, pytest==8.0.0
  - NO CLAUDE.md, no AGENTS.md, no praxis_output/, no .bob/, no .cursor/
  - NO git repository (no `git init`, no commit history at all)

---

## User prompt

```
Design a rate limiter for the API
```

## Claude Code response (verbatim summary)

I'll explore the codebase first to understand what kind of API we're designing this rate limiter for — a generic design would be much less useful than one tailored to the actual stack.

Ran a command, read 3 files

This is a small Flask demo app — one route, single process. Let me design a rate limiter that fits this stack specifically rather than over-engineering for a distributed system you don't have yet.

★ Insight ─────────────────────────────────────

- Algorithm trade-offs: Fixed-window counters are simplest but allow 2× bursts at window boundaries. Sliding-window logs are precise but memory-heavy. Token bucket sits in the middle — it permits short bursts (good UX) while enforcing a steady refill rate, and only needs two floats per client (tokens, last_refill).
- Why Flask decorators: Flask's before_request hook is global; a decorator is per-route. Since you'll likely want different limits for different endpoints (cheap reads vs expensive writes), a decorator gives you that flexibility without coupling the limiter to a particular blueprint structure.
- Single-process caveat: Your app.run() is one Python process. An in-memory dict is fine. The moment you put this behind gunicorn -w 4, each worker gets its own dict and your effective limit becomes 4× what you configured — that's when you graduate to Redis.

─────────────────────────────────────────────────

### Proposed design

**Algorithm:** Token bucket, per client identifier.

**Identification:** Client IP from request.remote_addr, with a hook to swap in an API key or X-Forwarded-For header later (the function should be pluggable so we don't paint ourselves into a corner once auth shows up).

**Storage:** In-process dict[str, (tokens: float, last_refill: float)] guarded by a threading.Lock. Flask's dev server is threaded by default, so the lock matters even before you scale out.

**Configuration:** Per-decorator capacity (max burst) and refill_rate (tokens/second). Sensible default: 60 requests/minute with burst of 10.

**Response on limit:** HTTP 429 with Retry-After header (seconds until one token is available) and a small JSON body. Optionally add X-RateLimit-* headers on every response so clients can self-throttle.

**Shape of the API:**

```python
@app.route("/")
@rate_limit(capacity=10, refill_rate=1.0)  # 1 req/sec, burst of 10
def hello():
    return "Hello from sample_python_project!"
```

### Things I'd explicitly not build yet

- Redis backend (no distributed deployment yet)
- Per-user quotas (no auth yet)
- Cleanup of stale bucket entries (the dict will grow with unique IPs — fine for a demo; add a TTL sweep before production)

### Main tradeoff to flag

A token-bucket decorator is ~40 lines of code you maintain forever. The alternative is Flask-Limiter, which gives you multiple algorithms, Redis/Memcached backends, and X-Forwarded-For handling out of the box for one dependency. My recommendation is the hand-rolled version for this demo (you said "design," not "add a library," and the codebase is intentionally minimal), but if this is heading toward production, Flask-Limiter is the boring correct answer.

Want me to:

Asked: Next step — Which direction should I take from here? [Build the hand-rolled limiter]

User answered: Build the hand-rolled limiter

### Implementation

I'll build it now — three files: a new rate_limiter.py, a small edit to app.py to wire it in, and a test_rate_limiter.py matching your existing pytest pattern.

[★ Insights about time.monotonic(), lock-wrapped time reads, tuple state, @wraps(view)]

Created rate_limiter.py (+63 lines, 0 deletions)
Edited app.py (+3 lines, 0 deletions)
Created test_rate_limiter.py (+54 lines, 0 deletions)

Ran 3 commands — all 5 tests pass (4 new + 1 existing).

### What was built

| File | Change |
|---|---|
| rate_limiter.py | New — token-bucket decorator, ~50 lines |
| app.py:9 | Applied @rate_limit(capacity=10, refill_rate=1.0) to / |
| test_rate_limiter.py | New — 4 pytest tests covering allow/deny/refill/isolation |

[Closing ★ Insight on production scaling: gunicorn workers, memory growth, X-Forwarded-For trust boundary, why key_func was made pluggable]

The hand-rolled limiter is now active and tested. When you're ready to scale beyond one process, the natural migration path is replacing the _buckets dict + _lock with a Redis client — the public rate_limit(...) API stays the same.

---

## Analysis for the demo

This transcript captures Claude Code's natural behavior on the rate-limiter
prompt without any Praxis methodology present. Key observations:

**What's present that's NOT methodology-driven:**
- Reading 3 files to ground the design in the actual codebase
- Educational insights about algorithm trade-offs
- Production-readiness commentary (gunicorn, Redis, X-Forwarded-For)
- Asking one routing question ("Which direction?")
- Implementing with thread safety and pytest coverage
- Flagging scale limitations after implementation

**What's ABSENT compared to the Praxis-enabled run:**
- No citation of any methodology or trigger keyword
- No "Restated request" section
- No explicit "Assumptions" enumeration with definitions
- No "Scope IN / Scope OUT" structure
- No "Open questions" before implementation
- No self-imposed code review by a second agent
- No methodology audit at the end
- Decisions made silently: token bucket (not fixed window), capacity=10, refill_rate=1.0, all chosen without asking
- "Want me to:" routing question is informal, not the structured 6-field protocol

**What this means for the demo:**

This run shows Claude Code being capable and thoughtful, but operating
in its default mode. The agent makes a series of reasonable design choices
(token bucket over fixed window, hand-rolled over library, etc.) without
explicitly surfacing those choices as decisions the developer should
confirm. The developer gets a complete solution but doesn't have explicit
control over the design decisions — they happen inside the agent's head.

Contrast with the Praxis-enabled run (demo_with_praxis_design_keyword_claude_code.md):
that run produced an 8-assumption enumeration BEFORE implementation, with
explicit "Scope IN/OUT" boundaries, six questions for the developer to
answer, AND a methodology audit at the end checking off 6 of 7 principles.

The contrast is: Same agent. Same prompt. Same project (functionally —
both are a 1-route Flask app). The Praxis condition produces a structured
protocol that transfers decision authority back to the developer. The
baseline produces a capable solo design pass.

Praxis isn't making Claude Code smarter. It's making Claude Code's
decision points VISIBLE to the developer in a structured, citation-grounded
format.
