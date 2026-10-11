# Lead access and customer data protection

## What changed

- **One access rule** in `crm/permissions.py`:
  - Managers (staff/superuser) see all leads.
  - An agent sees a lead only if it is assigned to them, or if it is unassigned and they created it.
  - Reassigning a lead removes the previous agent's access, including the creator's.
- **Customer contact masked** on deal list/detail, task list, call history, dashboard tasks and global search when the agent cannot see the lead. Template filters in `crm/templatetags/crm_access.py` (`lead_name`, `lead_phone`, `lead_initials`, `deal_title`, `can_view_lead`) apply the rule.
- **Property owner name and phone** visible only to managers, the assigned agent and the creator.
- **Lead CSV export** is manager-only. The export button is hidden from agents.
- **Agents cannot unassign a lead** (assignee field is required for non-managers).
- **Deal and task edit** keeps the record's current lead selectable, so an agent can edit a deal assigned to them even if its lead belongs to another agent.
- **Deleting a lead with deals** shows a clear message instead of a server error (`ProtectedError` handled).
- **Keyboard focus** is visible on all inputs and controls (`app.css`).

## Behaviour changes to know about

- Agents can no longer export CSV. Managers can.
- An agent who created a lead and later reassigned it no longer sees it.
- Agents' existing call history stays visible, but customer name and phone on those rows are masked if the agent no longer has the lead.

## Not changed yet

- `DEBUG` still defaults to True in `config/settings.py`. Changing it affects local setup, so it is a separate step.
- No "reveal phone" button with an audit log yet. This needs a new model and migration.
- Deal titles auto-generated from the customer name are masked on screen but still stored with the name.

## Commands to run

    python manage.py check
    python manage.py test

No new migrations were added. No model fields changed.
