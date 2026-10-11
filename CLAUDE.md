# Claude Code — Hartus Floare instructions

## Role
Act as a senior Django engineer, product designer, QA lead and pragmatic real-estate CRM product architect. Build carefully on the existing repository. Do not replace working code wholesale without first explaining the concrete problem and preserving current behavior.

## Project facts
- Python 3.12+, Django 6.1.1, server-rendered Django templates, SQLite local default; optional PostgreSQL through environment variables.
- Main app: `crm`; project config: `config/`.
- Core entities: `Lead`, `CallLog`, `Property`, `Deal`, `Task`.
- UI: responsive, editorial premium style; deep evergreen/navy sidebar, clean warm-neutral canvas, jade primary actions, restrained brass accents, legible typography and low-noise status colors.
- Main workflows: lead capture → call activity → qualification → property/deal linkage → follow-up task → won/lost result.
- Local setup and deployment cautions are documented in `README.md`.

## Non-negotiable engineering rules
1. Inspect files and run `python manage.py check` and `python manage.py test` before substantial changes. State the exact command results; never claim commands passed if they were not run.
2. Use Django ORM, `LoginRequiredMixin`, CSRF-protected POST requests and server-side validation. Never accept ownership/creator identifiers from user-submitted form fields.
3. Keep queryset authorization aligned between list, detail, update, delete, exports, related-object dropdowns and global search. Add tests for any permission-sensitive change.
4. Do not log or display passwords, secrets, tokens or full sensitive environment contents. Never hardcode real credentials or real customer data.
5. Use migrations for model changes; explain and include the migration command. Do not edit an already-shared migration destructively.
6. Use decimal values for money, explicit timezone-aware datetimes, database constraints/indexes where they materially help, and pagination for growing lists.
7. Keep views readable. Extract shared query scoping and repeated business logic instead of copy/pasting it.
8. Use semantic HTML, labels, keyboard focus indicators, responsive breakpoints, useful empty/error states and readable contrast. Motion must respect `prefers-reduced-motion`.
9. Do not state that calls, SMS, WhatsApp, email, AI recommendations, mapping, payments or external sync actually work unless a provider integration is implemented, configured and tested. Manual call activity logging is not a dialer.
10. Do not call this “world’s best” or guarantee an $80,000 valuation. Aim for enterprise-quality implementation while documenting what remains.

## Expected workflow
- Plan large changes with concise checkboxes.
- Read applicable files and focused Claude skills under `.claude/skills/`.
- Implement one coherent increment at a time.
- Add or update tests for behavior, permissions and edge cases.
- Run `python manage.py check`, `python manage.py test`, and Python compilation where useful.
- Review template rendering/URL reverses, HTML/JS console errors where a browser is available, and responsive states.
- Summarize changed files, commands actually run, known limitations, migration steps and next priorities.

## Definition of done for a feature
- Main happy path works.
- Empty, invalid, unauthorized and missing-record states are handled.
- Form errors appear adjacent to fields.
- Permissions are enforced server-side.
- Tests cover the business rule and the permission boundary.
- README is updated when setup/integration/deployment changes.
