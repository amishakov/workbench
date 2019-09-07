from datetime import date
from decimal import Decimal

from django.test import TestCase

from workbench import factories
from workbench.projects.models import Project
from workbench.projects.reporting import (
    hours_per_customer,
    overdrawn_projects,
    project_budget_statistics,
)
from workbench.reporting import key_data
from workbench.tools.models import Z


class StatisticsTest(TestCase):
    def test_stats(self):
        service1 = factories.ServiceFactory.create(effort_hours=2)
        factories.ServiceFactory.create(effort_hours=4)

        user = factories.UserFactory.create()

        op = list(overdrawn_projects())
        self.assertEqual(op, [])

        factories.LoggedHoursFactory.create(
            service=service1, created_by=user, rendered_by=user, hours=10
        )

        op = list(overdrawn_projects())
        self.assertEqual(len(op), 1)
        self.assertEqual(
            op,
            [
                {
                    "project": service1.project,
                    "logged_hours": Decimal("10.0"),
                    "service_hours": Decimal("2.0"),
                    "delta": Decimal("8.0"),
                }
            ],
        )

    def test_view(self):
        self.client.force_login(factories.UserFactory.create())
        response = self.client.get("/report/overdrawn-projects/")
        self.assertContains(response, "overdrawn projects")

        response = self.client.get("/report/hours-per-customer/")
        self.assertContains(response, "hours per customer")

        response = self.client.get("/report/hours-per-customer/?date_from=bla")
        self.assertRedirects(response, "/report/hours-per-customer/")

        response = self.client.get("/report/project-budget-statistics/")
        self.assertContains(response, "project budget statistics")

    def test_not_archived_hours_grouped_services_green_hours_hpc(self):
        service1 = factories.ServiceFactory.create(effort_rate=180, effort_type="Any")
        service2 = factories.ServiceFactory.create(project=service1.project)

        project = Project.objects.get()
        self.assertEqual(
            project.not_archived_total, {"total": Z, "hours_rate_undefined": Z}
        )

        factories.LoggedHoursFactory.create(service=service1, hours=10)
        factories.LoggedHoursFactory.create(service=service2, hours=20)

        project = Project.objects.get()
        self.assertEqual(
            project.not_archived_total,
            {"total": Decimal("1800.00"), "hours_rate_undefined": Decimal("20.00")},
        )

        invoice = factories.InvoiceFactory.create(
            project=project,
            customer=project.customer,
            contact=project.contact,
            type=factories.Invoice.SERVICES,
        )
        invoice.create_services_from_logbook(project.services.all())

        project = Project.objects.get()
        self.assertEqual(
            project.not_archived_total, {"total": Z, "hours_rate_undefined": Z}
        )

        hours = factories.LoggedHoursFactory.create(service=service1, hours=10)
        project = Project.objects.get()
        self.assertEqual(
            project.not_archived_total,
            {"total": Decimal("1800.00"), "hours_rate_undefined": Z},
        )

        self.assertEqual(project.project_invoices_total_excl_tax, Decimal("1800.00"))

        grouped = project.grouped_services
        self.assertEqual(len(grouped["offers"]), 1)
        self.assertIs(grouped["offers"][0][0], None)  # Offer is None
        self.assertEqual(grouped["logged_hours"], Decimal(40))
        self.assertEqual(grouped["service_hours"], 0)
        self.assertEqual(grouped["total_logged_cost"], Decimal(3600))
        self.assertEqual(grouped["total_service_cost"], 0)
        self.assertEqual(grouped["total_logged_hours_rate_undefined"], Decimal(20))
        self.assertEqual(grouped["total_service_hours_rate_undefined"], 0)

        today = date.today()
        date_range = [date(today.year, 1, 1), date(today.year, 12, 31)]

        green_hours = key_data.green_hours(date_range)
        gh = green_hours[today.year]["year"]
        self.assertEqual(gh.profitable, 0)
        self.assertEqual(gh.overdrawn, Decimal(40))
        self.assertEqual(gh.maintenance, 0)
        self.assertEqual(gh.internal, 0)
        self.assertEqual(gh.total, Decimal(40))
        self.assertEqual(gh.green, 0)

        hpc = hours_per_customer(date_range)
        self.assertEqual(hpc["organizations"][0]["total_hours"], Decimal(40))
        self.assertEqual(len(hpc["organizations"]), 1)
        self.assertEqual(len(hpc["users"]), 3)

        hpc = hours_per_customer(date_range, users=[hours.rendered_by])
        self.assertEqual(hpc["organizations"][0]["total_hours"], Decimal(10))
        self.assertEqual(len(hpc["organizations"]), 1)
        self.assertEqual(len(hpc["users"]), 1)

        stats = project_budget_statistics(Project.objects.all())
        self.assertEqual(
            stats,
            [
                {
                    "cost": Decimal("0.00"),
                    "effort_cost": Decimal("3600.000"),
                    "effort_hours_with_rate_undefined": Decimal("20.00"),
                    "invoiced": Decimal("1800.00"),
                    "logbook": Decimal("3600.000"),
                    "offered": Decimal("0.00"),
                    "project": project,
                    "third_party_costs": Decimal("0.00"),
                }
            ],
        )

    def test_green_hours(self):
        p_internal = factories.ProjectFactory.create(type=Project.INTERNAL)
        p_maintenance = factories.ProjectFactory.create(type=Project.MAINTENANCE)
        p_order = factories.ProjectFactory.create(type=Project.ORDER)

        s_internal = factories.ServiceFactory.create(project=p_internal)
        s_maintenance = factories.ServiceFactory.create(project=p_maintenance)
        s_order = factories.ServiceFactory.create(project=p_order, effort_hours=20)

        factories.LoggedHoursFactory.create(
            service=s_internal, hours=10, rendered_on=date(2019, 1, 1)
        )
        factories.LoggedHoursFactory.create(
            service=s_maintenance, hours=20, rendered_on=date(2019, 1, 1)
        )
        factories.LoggedHoursFactory.create(
            service=s_order, hours=5, rendered_on=date(2019, 1, 1)
        )
        factories.LoggedHoursFactory.create(
            service=s_order, hours=25, rendered_on=date(2019, 2, 1)
        )
        factories.LoggedHoursFactory.create(
            service=s_order, hours=10, rendered_on=date(2019, 3, 1)
        )

        factories.LoggedHoursFactory.create(
            service=s_order, hours=10, rendered_on=date(2018, 12, 1)
        )
        factories.LoggedHoursFactory.create(
            service=s_order, hours=10, rendered_on=date(2019, 4, 1)
        )

        gh = key_data.green_hours([date(2019, 1, 1), date(2019, 3, 31)])

        self.assertEqual(len(gh), 1)
        self.assertEqual(
            repr(gh[2019]["year"]),
            "<GreenHours profitable=10.00 overdrawn=30.00 maintenance=20.00"
            " internal=10.00 total=70.00 green=42%>",
        )

        self.assertEqual(
            repr(gh[2019]["months"][1]),
            "<GreenHours profitable=5.00 overdrawn=0.00 maintenance=20.00"
            " internal=10.00 total=35.00 green=71%>",
        )
        self.assertEqual(
            repr(gh[2019]["months"][2]),
            "<GreenHours profitable=5.00 overdrawn=20.00 maintenance=0.00"
            " internal=0.00 total=25.00 green=20%>",
        )
        self.assertEqual(
            repr(gh[2019]["months"][3]),
            "<GreenHours profitable=0.00 overdrawn=10.00 maintenance=0.00"
            " internal=0.00 total=10.00 green=0%>",
        )
