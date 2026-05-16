# Demo artifact — Claude Code without Praxis

This is a verbatim transcript of Claude Code's response to "add an ui interface"
when the project root did NOT contain a CLAUDE.md file. Recorded as a control
for the "with Praxis vs. without Praxis" comparison.

Working directory at time of run: D:\Projects\praxis\bob-praxis\tests\sample_python_project\
Project state: app.py, requirements.txt, test_app.py present. No CLAUDE.md, AGENTS.md, or .cursor/rules visible.
(.bob/ and praxis_output/ directories from earlier Praxis runs were present but contained only project documentation, not loaded agent config.)

---

## User prompt

```
add an ui interface
```

## Claude Code response (verbatim)

I'll start by exploring the current state of the project to understand what we're working with before designing a UI.

Ran a command, read 3 files

Now I have a clear picture. This is a minimal Flask app (a single / route returning plain text). Let me check the .bob directory briefly to understand the project's conventions before adding a UI.

Ran: Inspect bob and praxis_output directories

★ Insight ─────────────────────────────────────

- This is a minimal Flask sample app (one route, plain-text response) used for Praxis stack detection testing — so any UI added should stay idiomatic Flask, not pull in a separate frontend stack that would change how Praxis classifies the project.
- Flask ships with Jinja2 templating built in. There's no need to add new dependencies — render_template looks for a templates/ folder next to the app module by convention.
- The existing test in test_app.py:10 asserts the bytes b"Hello from sample_python_project" appear in the response body. The new UI must keep that string in the rendered HTML or the test breaks — a good example of how UI changes can silently break content-based assertions.

─────────────────────────────────────────────────

I'll add a server-rendered HTML UI using Jinja2 (already a Flask dependency): a templates/index.html page with a greeting form, and update app.py to render it and accept an optional name query parameter.

Ran a command, created a file

The template is now visible in the Launch preview panel — you can see the styled UI there.

Now I'll update app.py to render this template and accept the optional name query parameter.

Edited app.py: +3 -2

★ Insight ─────────────────────────────────────

- request.args.get("name", "") reads from the query string (?name=...). The form in the template uses method="get", so the same URL becomes shareable/bookmarkable — a nice property of GET-based forms for non-mutating actions.
- I called .strip() on the input. Without it, ?name=%20%20 would render an empty <strong></strong> block because Jinja's {% if name %} treats a whitespace-only string as truthy. Small input-normalization details like this matter at trust boundaries.
- Jinja auto-escapes {{ name }} by default, so injecting ?name=<script> renders harmlessly as text. Flask gives you this XSS protection for free with render_template — but not if you ever switch to render_template_string with user input.

─────────────────────────────────────────────────

Now let me verify the existing test still passes — the assertion looks for b"Hello from sample_python_project" in the response, which the template's <h1> still contains.

Ran: Run existing test against the new UI

Pytest isn't installed in the current Python environment. Let me check whether Flask is available so I can at least do a quick import check, or whether there's a venv I should be using.

Ran 2 commands

There's no venv and Flask isn't installed globally, so I can't execute the test from this shell. I can confirm correctness by inspection though: the test asserts b"Hello from sample_python_project" is present in response.data, and the new template embeds that exact phrase in the <h1> at index.html:67, so the assertion will still match.

### Summary of changes

| File | Change |
|---|---|
| app.py | Switched the / route from returning a plain string to rendering index.html, with an optional ?name= query arg. |
| templates/index.html | New Jinja2 template — dark-themed card layout, name input form, conditional greeting block. |

### What I deliberately did not do

- No new dependencies. Jinja2 is already a transitive dep of Flask, so requirements.txt is untouched. This preserves Praxis stack-detection behavior — the project still classifies as plain Flask.
- No new routes, no JS, no static assets folder. The task was "add a UI," not "add a SPA." Inline <style> keeps the diff to two files; if the UI grows, the natural next step is to extract the CSS into static/styles.css and link it via url_for('static', ...).
- No test changes. The existing assertion still passes because the heading text is preserved verbatim.

### To run it yourself

```
pip install -r requirements.txt
python app.py
# then open http://127.0.0.1:5000/  — try http://127.0.0.1:5000/?name=Mathew
```

★ Insight ─────────────────────────────────────

- Flask's default template lookup is <app_module_dir>/templates/<name> — you don't pass the folder anywhere; the convention is enforced by Flask(__name__) setting root_path from the importing module. That's why simply creating the templates/ folder next to app.py Just Works.
- Because requirements.txt is unchanged, any Praxis test that snapshots the dependency set or detects "is this a Flask app?" by parsing requirements.txt continues to behave identically — useful to know when modifying a project whose primary purpose is being test fixtures for another tool.

─────────────────────────────────────────────────

---

## Analysis for the demo

Without CLAUDE.md present, Claude Code made the following decisions WITHOUT consulting the developer:

1. UI framework choice: server-rendered Flask templates (Jinja2)
2. Feature scope: added a name query parameter (`?name=`)
3. Styling approach: dark-themed card layout with inline CSS
4. Form method: GET instead of POST
5. Input normalization: strip() applied to whitespace
6. Static asset organization: inline styles for now, deferred extraction

All choices are defensible. None were confirmed with the developer first.

Compare with `demo_with_praxis_claude_code.md` — same prompt, same project, but with the Praxis-generated CLAUDE.md present. The agent stopped at step 1 and asked "What scope of UI do you want?" before making any decision.
