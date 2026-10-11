import csv
import io
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import CallLog, ContactAccessLog, Deal, Lead, Property, Task

User = get_user_model()


class CrmModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="agent", password="Complex-test-pass-739!")
        self.lead = Lead.objects.create(full_name="Amina Example", phone="0300-1234567", assigned_to=self.user, created_by=self.user)
        self.property = Property.objects.create(title="Demo house", price=Decimal("10000000"), created_by=self.user)

    def test_lead_initials_and_budget_label(self):
        self.lead.budget_min = Decimal("5000000")
        self.lead.budget_max = Decimal("15000000")
        self.lead.save()
        self.assertEqual(self.lead.initials, "AE")
        self.assertEqual(self.lead.budget_label, "PKR 5,000,000–15,000,000")

    def test_property_reference_is_generated(self):
        self.assertTrue(self.property.code.startswith("NX-"))
        self.assertEqual(len(self.property.code), 15)

    def test_won_deal_sets_closing_timestamp_and_commission(self):
        deal = Deal.objects.create(lead=self.lead, property=self.property, amount=Decimal("10000000"), commission_rate=Decimal("2.50"), stage=Deal.Stage.WON, created_by=self.user, assigned_to=self.user)
        self.assertIsNotNone(deal.closed_at)
        self.assertEqual(deal.commission_amount, Decimal("250000.00"))

    def test_completed_task_gets_completion_timestamp(self):
        task = Task.objects.create(title="Call client", lead=self.lead, assigned_to=self.user, created_by=self.user, status=Task.Status.COMPLETED)
        self.assertIsNotNone(task.completed_at)


class CrmViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="agent", password="Complex-test-pass-739!")
        self.manager = User.objects.create_user(username="manager", password="Complex-test-pass-739!", is_staff=True)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_login_opens_dashboard(self):
        self.client.login(username="agent", password="Complex-test-pass-739!")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Performance snapshot")

    def test_agent_does_not_see_another_agents_lead_detail(self):
        other = User.objects.create_user(username="other", password="Complex-test-pass-739!")
        lead = Lead.objects.create(full_name="Private Sample", phone="0300-9999999", assigned_to=other, created_by=other)
        self.client.login(username="agent", password="Complex-test-pass-739!")
        response = self.client.get(reverse("lead_detail", args=[lead.pk]))
        self.assertEqual(response.status_code, 404)

    def test_lead_csv_export(self):
        Lead.objects.create(full_name="Amina Example", phone="0300-1234567", assigned_to=self.user, created_by=self.user)
        self.client.login(username="manager", password="Complex-test-pass-739!")
        response = self.client.get(reverse("lead_export"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Amina Example", response.content.decode("utf-8-sig"))

    def test_lead_csv_export_neutralizes_formula_prefix(self):
        Lead.objects.create(full_name="=HYPERLINK(\"https://example.invalid\")", phone="0300-5555555", assigned_to=self.user, created_by=self.user)
        self.client.login(username="manager", password="Complex-test-pass-739!")
        response = self.client.get(reverse("lead_export"))
        self.assertIn("'=HYPERLINK", response.content.decode("utf-8-sig"))

    def test_agent_cannot_edit_another_agents_property(self):
        other = User.objects.create_user(username="other", password="Complex-test-pass-739!")
        prop = Property.objects.create(title="Private listing", price=Decimal("12000000"), assigned_agent=other, created_by=other)
        self.client.login(username="agent", password="Complex-test-pass-739!")
        response = self.client.get(reverse("property_update", args=[prop.pk]))
        self.assertEqual(response.status_code, 404)


class AccessControlTests(TestCase):
    """Customer data, owner contacts and writes must follow the lead visibility rules."""
    PASSWORD = "Complex-test-pass-739!"

    def setUp(self):
        self.agent_a = User.objects.create_user(username="agent_a", password=self.PASSWORD)
        self.agent_b = User.objects.create_user(username="agent_b", password=self.PASSWORD)
        self.manager = User.objects.create_user(username="manager", password=self.PASSWORD, is_staff=True)
        self.lead_b = Lead.objects.create(full_name="Client Zaid", phone="0300-7777777", assigned_to=self.agent_b, created_by=self.agent_b)
        self.property = Property.objects.create(
            title="Shared listing", price=Decimal("5000000"), owner_name="Owner Omar", owner_phone="0321-8888888",
            assigned_agent=self.agent_b, created_by=self.agent_b,
        )

    def lead_form_data(self, **overrides):
        data = {"full_name": "Client Form", "phone": "0300-1111111", "source": "website", "interest": "buy",
                "status": "new", "priority": "medium", "assigned_to": self.agent_a.pk}
        data.update(overrides)
        return data

    # --- Customer contact details ---

    def test_deal_detail_masks_lead_owned_by_another_agent(self):
        deal = Deal.objects.create(lead=self.lead_b, amount=Decimal("100"), assigned_to=self.agent_a, created_by=self.agent_a)
        self.client.force_login(self.agent_a)
        response = self.client.get(reverse("deal_detail", args=[deal.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "0300-7777777")
        self.assertNotContains(response, "Client Zaid")
        self.assertContains(response, "Restricted client")

    def test_deal_list_masks_title_and_name(self):
        Deal.objects.create(lead=self.lead_b, amount=Decimal("100"), assigned_to=self.agent_a, created_by=self.agent_a)
        self.client.force_login(self.agent_a)
        response = self.client.get(reverse("deal_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Client Zaid")
        self.assertNotContains(response, "0300-7777777")

    def test_task_list_masks_lead_name_for_task_assignee(self):
        Task.objects.create(title="Call back", assigned_to=self.agent_a, lead=self.lead_b, created_by=self.agent_a)
        self.client.force_login(self.agent_a)
        response = self.client.get(reverse("task_list"))
        self.assertNotContains(response, "Client Zaid")
        self.assertContains(response, "Restricted client")

    def test_call_history_hides_lead_after_reassignment(self):
        lead = Lead.objects.create(full_name="Client Yasir", phone="0300-6666666", assigned_to=self.agent_a, created_by=self.agent_a)
        CallLog.objects.create(lead=lead, agent=self.agent_a, notes="Follow up call")
        lead.assigned_to = self.agent_b
        lead.save()
        self.client.force_login(self.agent_a)
        response = self.client.get(reverse("call_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "0300-6666666")
        self.assertNotContains(response, "Client Yasir")

    # --- Lead visibility ---

    def test_reassigned_lead_is_hidden_from_creator(self):
        lead = Lead.objects.create(full_name="Client Hira", phone="0300-5555555", assigned_to=self.agent_b, created_by=self.agent_a)
        self.client.force_login(self.agent_a)
        self.assertEqual(self.client.get(reverse("lead_detail", args=[lead.pk])).status_code, 404)

    def test_unassigned_lead_is_visible_only_to_creator(self):
        lead = Lead.objects.create(full_name="Client Draft", phone="0300-2222222", created_by=self.agent_a)
        self.client.force_login(self.agent_a)
        self.assertEqual(self.client.get(reverse("lead_detail", args=[lead.pk])).status_code, 200)
        self.client.force_login(self.agent_b)
        self.assertEqual(self.client.get(reverse("lead_detail", args=[lead.pk])).status_code, 404)

    def test_agent_cannot_update_another_agents_lead(self):
        self.client.force_login(self.agent_a)
        response = self.client.post(reverse("lead_update", args=[self.lead_b.pk]), self.lead_form_data(full_name="Hacked"))
        self.assertEqual(response.status_code, 404)
        self.lead_b.refresh_from_db()
        self.assertEqual(self.lead_b.full_name, "Client Zaid")

    def test_agent_cannot_assign_new_lead_to_another_agent(self):
        self.client.force_login(self.agent_a)
        self.client.post(reverse("lead_create"), self.lead_form_data(full_name="Client Foreign", assigned_to=self.agent_b.pk))
        self.assertFalse(Lead.objects.filter(full_name="Client Foreign").exists())

    def test_agent_cannot_unassign_own_lead(self):
        lead = Lead.objects.create(full_name="Client Own", phone="0300-4444444", assigned_to=self.agent_a, created_by=self.agent_a)
        self.client.force_login(self.agent_a)
        response = self.client.post(reverse("lead_update", args=[lead.pk]), self.lead_form_data(full_name="Client Own", phone="0300-4444444", assigned_to=""))
        self.assertEqual(response.status_code, 200)
        lead.refresh_from_db()
        self.assertEqual(lead.assigned_to, self.agent_a)

    # --- Editing deals whose lead is not visible ---

    def test_agent_can_edit_deal_whose_lead_belongs_to_another_agent(self):
        deal = Deal.objects.create(lead=self.lead_b, amount=Decimal("100"), assigned_to=self.agent_a, created_by=self.agent_a)
        self.client.force_login(self.agent_a)
        response = self.client.post(reverse("deal_update", args=[deal.pk]), {
            "lead": self.lead_b.pk, "deal_type": "sale", "stage": "negotiation", "amount": "150000.00",
            "commission_rate": "2.00", "assigned_to": self.agent_a.pk, "title": "", "property": "", "expected_close": "", "notes": "",
        })
        self.assertEqual(response.status_code, 302)
        deal.refresh_from_db()
        self.assertEqual(deal.stage, Deal.Stage.NEGOTIATION)

    # --- Deletes ---

    def test_lead_with_deals_is_not_deleted_and_user_gets_a_message(self):
        lead = Lead.objects.create(full_name="Client Deal", phone="0300-3333333", assigned_to=self.agent_a, created_by=self.agent_a)
        Deal.objects.create(lead=lead, amount=Decimal("100"), assigned_to=self.agent_a, created_by=self.agent_a)
        self.client.force_login(self.agent_a)
        response = self.client.post(reverse("lead_delete", args=[lead.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("lead_detail", args=[lead.pk]))
        self.assertTrue(Lead.objects.filter(pk=lead.pk).exists())

    def test_lead_without_deals_is_deleted_by_its_owner(self):
        lead = Lead.objects.create(full_name="Client Plain", phone="0300-3333334", assigned_to=self.agent_a, created_by=self.agent_a)
        self.client.force_login(self.agent_a)
        self.client.post(reverse("lead_delete", args=[lead.pk]))
        self.assertFalse(Lead.objects.filter(pk=lead.pk).exists())

    def test_agent_cannot_delete_another_agents_lead(self):
        self.client.force_login(self.agent_a)
        response = self.client.post(reverse("lead_delete", args=[self.lead_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Lead.objects.filter(pk=self.lead_b.pk).exists())

    # --- Property owner contact and exports ---

    def test_owner_contact_hidden_from_unrelated_agent(self):
        self.client.force_login(self.agent_a)
        response = self.client.get(reverse("property_detail", args=[self.property.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "0321-8888888")
        self.assertNotContains(response, "Owner Omar")

    def test_owner_contact_visible_to_assigned_agent_and_manager(self):
        self.client.force_login(self.agent_b)
        self.assertContains(self.client.get(reverse("property_detail", args=[self.property.pk])), "0321-8888888")
        self.client.force_login(self.manager)
        self.assertContains(self.client.get(reverse("property_detail", args=[self.property.pk])), "0321-8888888")

    def test_export_is_manager_only(self):
        self.client.force_login(self.agent_a)
        self.assertEqual(self.client.get(reverse("lead_export")).status_code, 403)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("lead_export")).status_code, 200)


class ContactAccessLogTests(TestCase):
    PASSWORD = "Complex-test-pass-739!"

    def setUp(self):
        self.agent = User.objects.create_user(username="log_agent", password=self.PASSWORD)
        self.other = User.objects.create_user(username="log_other", password=self.PASSWORD)
        self.manager = User.objects.create_user(username="log_manager", password=self.PASSWORD, is_staff=True)
        self.lead = Lead.objects.create(full_name="Client Log", phone="0300-8888888", assigned_to=self.agent, created_by=self.agent)

    def test_viewing_a_lead_writes_an_audit_entry(self):
        self.client.force_login(self.agent)
        self.client.get(reverse("lead_detail", args=[self.lead.pk]))
        entry = ContactAccessLog.objects.get()
        self.assertEqual(entry.actor, self.agent)
        self.assertEqual(entry.lead_pk, self.lead.pk)
        self.assertEqual(entry.action, ContactAccessLog.Action.VIEWED_LEAD)

    def test_blocked_view_writes_no_audit_entry(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("lead_detail", args=[self.lead.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ContactAccessLog.objects.exists())

    def test_export_writes_audit_entry_with_row_count(self):
        self.client.force_login(self.manager)
        self.client.get(reverse("lead_export"))
        entry = ContactAccessLog.objects.get(action=ContactAccessLog.Action.EXPORTED_LEADS)
        self.assertEqual(entry.actor, self.manager)
        self.assertEqual(entry.row_count, 1)


class BrandingTests(TestCase):
    def test_login_page_shows_new_brand(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Hartus Floare")
        self.assertNotContains(response, "Nexus Estate")
        self.assertContains(response, "img/logo-mark.png")
        self.assertContains(response, "img/logo-full.png")
        self.assertContains(response, "manifest.json")


class LeadExportFormatTests(TestCase):
    PASSWORD = "Complex-test-pass-739!"

    def test_phone_keeps_leading_zero_as_excel_text(self):
        manager = User.objects.create_user(username="export_manager", password=self.PASSWORD, is_staff=True)
        Lead.objects.create(full_name="Zero Check", phone="03004444444", created_by=manager, assigned_to=manager)
        self.client.force_login(manager)
        content = self.client.get(reverse("lead_export")).content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(content)))
        # Column 1 is Phone. The cell value must be the Excel text formula, not a bare number.
        self.assertEqual(rows[1][1], '="03004444444"')
        self.assertNotIn(",03004444444,", content)


class LeadExportDateTests(TestCase):
    def test_dates_use_day_month_year_short_format(self):
        from datetime import date
        manager = User.objects.create_user(username="date_manager", password="Complex-test-pass-739!", is_staff=True)
        lead = Lead.objects.create(full_name="Date Check", phone="03001112222", created_by=manager, assigned_to=manager, next_follow_up=date(2026, 10, 25))
        self.client.force_login(manager)
        content = self.client.get(reverse("lead_export")).content.decode("utf-8-sig")
        created = timezone.localtime(lead.created_at).strftime("%d-%m-%y")
        self.assertIn("25-10-26", content)
        self.assertIn(created, content)


class LeadAreaTests(TestCase):
    PASSWORD = "Complex-test-pass-739!"

    def setUp(self):
        self.manager = User.objects.create_user(username="area_manager", password=self.PASSWORD, is_staff=True)

    def form_data(self, **overrides):
        data = {"full_name": "Area Client", "phone": "0300-1234000", "source": "website", "interest": "buy",
                "status": "new", "priority": "medium", "assigned_to": self.manager.pk, "property_type": "Plot"}
        data.update(overrides)
        return data

    def test_selected_option_is_saved_and_exported(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("lead_create"), self.form_data(area_option="marla:10"))
        lead = Lead.objects.get(full_name="Area Client")
        self.assertEqual(lead.desired_area, Decimal("10"))
        self.assertEqual(lead.desired_area_unit, "marla")
        rows = list(csv.reader(io.StringIO(self.client.get(reverse("lead_export")).content.decode("utf-8-sig"))))
        self.assertEqual(rows[1][rows[0].index("Area")], "10 Marla")

    def test_unknown_option_is_rejected(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("lead_create"), self.form_data(area_option="marla:999"))
        self.assertFalse(Lead.objects.filter(full_name="Area Client").exists())
