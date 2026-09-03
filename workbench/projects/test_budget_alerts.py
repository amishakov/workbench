import datetime as dt
from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.utils.translation import deactivate_all

from workbench import factories
from workbench.projects.models import Project
from workbench.projects.tasks import send_budget_alerts


class BudgetAlertsTest(TestCase):
    def setUp(self):
        deactivate_all()

    def log_cost(self, project, cost):
        service = factories.ServiceFactory.create(project=project)
        factories.LoggedCostFactory.create(service=service, cost=cost)

    def test_no_alert_without_threshold(self):
        """Projects without a threshold are never alerted about"""
        project = factories.ProjectFactory.create()
        self.log_cost(project, Decimal(1000))

        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 0)

    def test_alert_is_sent_once(self):
        """The alert fires when the threshold is reached, and only once"""
        project = factories.ProjectFactory.create(budget_alert_at=Decimal(500))
        self.log_cost(project, Decimal(400))

        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 0)

        self.log_cost(project, Decimal(150))
        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [project.owned_by.email])
        self.assertIn(project.get_absolute_url(), mail.outbox[0].body)

        project.refresh_from_db()
        self.assertIsNotNone(project.budget_alert_sent_at)

        # No second mail for the same threshold.
        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 1)

    def test_new_threshold_arms_the_alert_again(self):
        """Saving a new threshold clears the sent marker"""
        project = factories.ProjectFactory.create(budget_alert_at=Decimal(500))
        self.log_cost(project, Decimal(600))

        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 1)

        project = Project.objects.get(pk=project.pk)
        project.budget_alert_at = Decimal(1000)
        project.save()
        self.assertIsNone(project.budget_alert_sent_at)

        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 1)  # 600 < 1000

        self.log_cost(project, Decimal(500))
        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 2)

    def test_saving_something_else_keeps_the_sent_marker(self):
        """Unrelated changes do not re-arm the alert"""
        project = factories.ProjectFactory.create(budget_alert_at=Decimal(500))
        self.log_cost(project, Decimal(600))

        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 1)

        project = Project.objects.get(pk=project.pk)
        project.title = "Something else"
        project.save()
        self.assertIsNotNone(project.budget_alert_sent_at)

        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 1)

    def test_closed_projects_are_skipped(self):
        """Closed projects do not produce alerts anymore"""
        project = factories.ProjectFactory.create(
            budget_alert_at=Decimal(500), closed_on=dt.date.today()
        )
        self.log_cost(project, Decimal(600))

        send_budget_alerts()
        self.assertEqual(len(mail.outbox), 0)
