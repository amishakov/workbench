from django.conf import settings
from django.core.management import BaseCommand
from django.utils.translation import activate

from workbench.accounts.middleware import set_user_name
from workbench.accounts.tasks import coffee_invites, work_anniversaries_notice
from workbench.audit.tasks import prune_audit
from workbench.awt.tasks import annual_working_time_warnings_mails
from workbench.invoices.tasks import (
    create_recurring_invoices_and_notify,
    send_unsent_projected_invoices_reminders,
    tuesday_autodunning,
)
from workbench.planning.updates import changes_mails
from workbench.reporting.tasks import create_accruals_for_last_month


class Command(BaseCommand):
    help = "Fairy tasks"

    def handle(self, **options):
        activate(settings.WORKBENCH.PDF_LANGUAGE)
        set_user_name("Fairy tasks")
        create_accruals_for_last_month()
        create_recurring_invoices_and_notify()
        coffee_invites()
        changes_mails()
        annual_working_time_warnings_mails()
        send_unsent_projected_invoices_reminders()
        tuesday_autodunning()
        prune_audit()
        work_anniversaries_notice()
