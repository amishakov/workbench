from collections import defaultdict

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.utils.translation import gettext as _

from workbench.projects.models import Project
from workbench.reporting.project_budget_statistics import project_budget_statistics
from workbench.tools.formats import currency


BUDGET_ALERT_TEMPLATE = """\
{project}
{base_url}{project_url}
{logbook_label}: {logbook}
{alert_at_label}: {alert_at}
{sold_label}: {sold}
"""


def send_budget_alerts():
    """
    Notify project owners when the logged cost of a project reaches the
    threshold they configured on the project.

    The mail is sent once per threshold; setting a new threshold on the project
    arms the alert again.
    """
    projects = list(
        Project.objects.open().filter(
            budget_alert_at__isnull=False, budget_alert_sent_at__isnull=True
        )
    )
    if not projects:
        return

    statistics = project_budget_statistics(projects)["statistics"]
    reached = [s for s in statistics if s["logbook"] >= s["project"].budget_alert_at]
    if not reached:
        return

    by_owner = defaultdict(list)
    for stat in reached:
        by_owner[stat["project"].owned_by].append(stat)

    for user, stats in by_owner.items():
        body = "\n\n".join(
            BUDGET_ALERT_TEMPLATE.format(
                project=stat["project"],
                base_url=settings.WORKBENCH.URL,
                project_url=stat["project"].get_absolute_url(),
                logbook_label=_("Logbook"),
                logbook=currency(stat["logbook"]),
                alert_at_label=_("Alert at"),
                alert_at=currency(stat["project"].budget_alert_at),
                sold_label=_("Sold"),
                sold=currency(stat["sold"]),
            )
            for stat in stats
        )
        EmailMultiAlternatives(
            _("Budget alert"),
            f"""\
Hallo {user}

Bei folgenden Projekten wurde der von Dir hinterlegte Betrag erreicht:

{body}

Bitte prüfe, ob das Kostendach erhöht werden muss oder ob Du
mit der Kundschaft Kontakt aufnehmen möchtest.

Diese Meldung erscheint einmal pro hinterlegtem Betrag. Wenn Du
erneut gewarnt werden möchtest, hinterlege einen neuen Betrag.
""",
            to=[user.email],
            reply_to=[user.email],
        ).send()

    now = timezone.now()
    Project.objects.filter(id__in=[stat["project"].id for stat in reached]).update(
        budget_alert_sent_at=now
    )
