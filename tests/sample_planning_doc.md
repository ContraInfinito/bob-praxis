# Habit Tracker API

A backend REST API for tracking daily habits. Users log habit completions, view streak data, and see weekly stats. Multi-user with personal accounts. The goal is a small, focused service that does one thing well and can be deployed on a single small VM.

## Stack

- Python 3.11+
- Flask for the HTTP layer (chosen over FastAPI for team familiarity)
- pytest for the test suite
- SQLAlchemy for ORM
- Alembic for schema migrations
- marshmallow for request/response serialization

## Features

- User registration and login (email + password)
- Create habits with a name, description, and target frequency (daily, weekly, custom)
- Log a habit completion for a given date
- View current streak and longest streak per habit
- Weekly stats endpoint: completions per habit, completion rate
- Soft-delete habits (preserve history, hide from active list)

## Integrations

- **PostgreSQL** for primary data storage. Tables: users, habits, completions. Foreign keys with cascade-delete on user removal (except where soft-delete applies).
- **SendGrid** for transactional email. Used for password reset flows and an optional weekly digest email.
- **Sentry** for error tracking in production. Captures unhandled exceptions and integrates with Flask's error handlers.

## Data Model

The core entities are User, Habit, and Completion. A User has many Habits. A Habit has many Completions. Each Completion is a single row tying a Habit to a date.

Streaks are computed from Completions on read, not stored. For a daily habit, the streak is the count of consecutive days ending today (or yesterday) with at least one Completion. For weekly habits, the streak is the count of consecutive weeks meeting the target frequency. Custom-frequency habits (e.g., "3 times per week") use the same logic adapted to the target.

We need to decide how to handle timezones. Completions are stored as UTC dates, but a user logging "I did this today" expects "today" to mean their local day. Either we store the user's timezone on the User record and convert on write, or we accept a date parameter from the client and trust it. The right choice depends on whether we want a single source of truth on the server or flexibility for clients.

## API Surface

REST conventions throughout. JSON request and response bodies. JWT tokens for authentication.

Main endpoints:
- `POST /auth/register`, `POST /auth/login`, `POST /auth/reset`
- `GET /habits`, `POST /habits`, `GET /habits/<id>`, `PATCH /habits/<id>`, `DELETE /habits/<id>` (soft delete)
- `POST /habits/<id>/completions`, `GET /habits/<id>/completions`
- `GET /habits/<id>/streak`, `GET /habits/<id>/stats?period=week`

The streak and stats endpoints are read-heavy. We may need to add caching later if performance becomes a concern.

## What's Out of Scope (v1)

- Mobile apps. The API is the deliverable; client apps come later.
- Social features (following other users, public profiles, leaderboards). Single-user focus only.
- Reminder notifications (push or SMS). Email digests only, no real-time alerts.
- Habit templates or shared habit definitions. Each user defines their own habits.

## Open Questions

A few things deliberately unspecified — they need decisions before the first feature ships, but the planning phase isn't the right place to make them. Whoever picks up implementation should resolve these with the product owner before writing code.