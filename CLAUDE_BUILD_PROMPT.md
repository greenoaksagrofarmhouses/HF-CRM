# Claude Code prompt — Hartus Floare

Paste this into Claude Code after opening the `nexus_estate_crm` project directory. The repository also contains `CLAUDE.md` and focused skills in `.claude/skills/`.

---

You are the senior engineering team responsible for evolving **Hartus Floare**, a polished real-estate CRM built with Python 3.12+, Django 6.1.1, server-rendered templates and a responsive custom CSS design system. The target quality is premium enterprise software: trustworthy, cohesive, fast for everyday agents, accessible, secure and easy to maintain. Do not make claims about a monetary valuation; prove quality through behavior, tests and UX.

## First task: audit before changing
1. Read `CLAUDE.md`, `README.md`, and each applicable skill under `.claude/skills/`.
2. Inspect the entire repository. Run `python manage.py check`, `python manage.py test`, and `python -m compileall config crm manage.py` if the environment and dependencies permit.
3. Create a short priority list of confirmed bugs, missing migrations, authorization gaps, accessibility problems, UX gaps and unimplemented integrations. Distinguish confirmed findings from assumptions.
4. Fix actual blockers first. Never rewrite the entire project merely to change style. Preserve working workflows and backwards compatibility.

## Product outcome
The product should support this path without unnecessary clicks:
**Lead capture → call activity → qualification → property match/viewing → deal negotiation → won/lost → follow-up and reporting.**

## Current core modules
- Overview dashboard with metrics, stage distribution, recent leads, calls, upcoming tasks and six-month won-deal value chart.
- Leads: contact details, source, intent, property requirements, budget range, preferred location, priority, status, owner/assignee, notes and next follow-up.
- Manual call logging with direction, outcome, duration, notes and follow-up date.
- Property inventory for sale and rental listings, type, availability, price, location, size, rooms, owner details, unique reference code and assigned agent.
- Deals with lead/property relationship, separate stage, deal amount, expected closing and configurable commission percentage.
- Tasks with assignee, due date, priority, status and linked lead/property.
- Global search, lead CSV export, Django admin, login/logout and synthetic seed data.

## High-value upgrade order
1. Make initial migrations a committed, clean baseline. Confirm all fresh-database install steps work from an empty directory/database.
2. Inspect every permission boundary and add a consistent permission service. List pages, detail pages, update/delete endpoints, autocomplete dropdowns, related lists, exports and search must agree. Document role rules clearly.
3. Add robust tests for form validation, duplicates, task completion, stage transitions, date boundaries, CSV export, object scoping and users trying to submit foreign IDs.
4. Add deduplicated CSV lead import with preview, column mapping, per-row validation, error download and a confirmation step. Do not partially import invalid files silently.
5. Improve the lead/deal pipeline experience with a keyboard-accessible board/list toggle, safe stage changes, filter persistence and sensible mobile behavior.
6. Add a property viewing/appointment entity if the domain requirements justify it; avoid overloading Task for appointment-specific fields.
7. Add activity/audit history for sensitive lifecycle changes with actor and timestamp; do not log passwords, tokens or unnecessary sensitive data.
8. Improve analytics with explicit date ranges and labels separating deal value, actual company revenue and commission. Add timezone-aware date filtering.
9. Consider REST API/OpenAPI only when there is a real integration consumer. Add object-level API permissions, pagination, throttling and tests before exposing it.
10. Add deployment/CI documentation, dependency checks, backup/restore tests and PostgreSQL validation.

## Design bar
- Keep the evergreen/navy sidebar, jade primary actions, warm-neutral canvas and restrained brass accents, but prioritize contrast and usability over decoration.
- Make key actions discoverable: Add lead, Log call, Schedule follow-up, Create deal and Add property.
- Add good loading/empty/error states, in-context field errors, confirmation for destructive actions, responsive behavior and accessible keyboard focus.
- Maintain a consistent spacing/type/field/button/table/status system. Avoid one-off inline styling unless it encodes simple dynamic data.
- Do not depend on an external CDN for critical behavior. If fonts/icons/charts are optional external assets, ensure content remains usable without them.

## Technical constraints
- Use Django ORM and migrations. Use `DecimalField` for money, explicit timezone-aware datetimes, pagination and query optimization where useful.
- Keep CSRF, auth, session, secure settings and server-side authorization. Use POST for state changes.
- Keep secrets outside Git; production must set a strong secret key, `DEBUG=False`, correct host/origin settings, HTTPS and a managed database.
- Treat client/contact/listing information as confidential. No real contact details in fixtures, examples or screenshots.
- Do not wire external email, SMS, WhatsApp, telephony, AI, payment or maps behavior without named providers, credentials/configuration, failure handling and tests. Manual call logs are not live calls.
- If adding dependencies, justify each, pin tested compatible versions and document installation.
- Support Python 3.12+ as indicated in the project docs; validate the selected Django version’s official compatibility/security notes before changing it.

## Delivery rules
For every increment:
1. Explain the goal briefly.
2. Make a focused change.
3. Add/adjust tests.
4. Run checks and tests; if impossible because dependencies/network are missing, say so explicitly and do not imply success.
5. Review URLs referenced by templates and authorization of related records.
6. Summarize changed files, migrations/commands, actual test results and remaining work.

Start now with the repository audit. Then fix the highest-impact verified issues and complete one cohesive increment fully before moving to the next.
