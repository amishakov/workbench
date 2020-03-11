from collections import defaultdict
from itertools import chain, groupby

from django.db import connections
from django.db.models import Sum

from workbench.accounts.models import User
from workbench.logbook.models import LoggedCost
from workbench.projects.models import Project
from workbench.tools.models import Z


SQL = """
select
    p.id,
    hourly_labor_costs,
    green_hours_target,
    lh.rendered_by_id,
    sum(lh.hours) as hours
from logbook_loggedhours lh
left join projects_service ps on lh.service_id=ps.id
left join projects_project p on ps.project_id=p.id
left outer join lateral (select * from awt_employment) as costs on
lh.rendered_by_id=costs.user_id
and lh.rendered_on >= costs.date_from
and lh.rendered_on <= costs.date_until
where %s
group by p.id, hourly_labor_costs, green_hours_target, lh.rendered_by_id
"""

USER_KEYS = [
    "hours",
    "hours_with_rate_undefined",
    "costs",
    "costs_with_green_hours_target",
]
PROJECT_KEYS = USER_KEYS + ["third_party_costs"]


def _labor_costs_by_project_id(date_range, *, where=None, params=None):
    projects = defaultdict(
        lambda: {
            "hours": Z,
            "hours_with_rate_undefined": Z,
            "costs": Z,
            "costs_with_green_hours_target": Z,
            "third_party_costs": Z,
            "by_user": defaultdict(
                lambda: {
                    "hours": Z,
                    "hours_with_rate_undefined": Z,
                    "costs": Z,
                    "costs_with_green_hours_target": Z,
                }
            ),
        }
    )

    with connections["default"].cursor() as cursor:
        where = where or []
        where.append("lh.rendered_on >= %s and lh.rendered_on <= %s")
        params = params or []
        params.extend(date_range)
        cursor.execute(SQL % " and ".join(where), params)

        for project_id, hlc, ght, rendered_by_id, hours in cursor:
            project = projects[project_id]
            project["hours"] += hours

            by_user = project["by_user"][rendered_by_id]
            by_user["hours"] += hours

            if hlc is None:
                project["hours_with_rate_undefined"] += hours
                by_user["hours_with_rate_undefined"] += hours

            else:
                costs = hours * hlc
                costs_with_ght = hours * hlc * 100 / ght

                project["costs"] += costs
                project["costs_with_green_hours_target"] += costs_with_ght

                by_user["costs"] += costs
                by_user["costs_with_green_hours_target"] += costs_with_ght

    queryset = LoggedCost.objects.order_by().filter(
        rendered_on__range=date_range, third_party_costs__isnull=False
    )

    # FIXME Do this properly
    if "cost_center" in where[0]:
        queryset = queryset.filter(service__project__cost_center=params[0])
    if "project" in where[0]:
        queryset = queryset.filter(service__project=params[1])

    for row in queryset.values("service__project").annotate(
        cost=Sum("third_party_costs")
    ):
        project = projects[row["service__project"]]
        project["third_party_costs"] += row["cost"]

    return projects


def labor_costs_by_cost_center(date_range):
    projects = _labor_costs_by_project_id(date_range)

    sorted_projects = sorted(
        [
            {"project": project, **projects[project.id]}
            for project in Project.objects.filter(
                id__in=projects.keys()
            ).select_related("cost_center", "owned_by")
        ],
        key=lambda row: (row["project"].cost_center_id or 1e100, -row["costs"]),
    )

    cost_centers = []
    for cost_center, cc_projects in groupby(
        sorted_projects, lambda row: row["project"].cost_center
    ):
        cc_projects = list(cc_projects)
        cc_row = {key: sum(row[key] for row in cc_projects) for key in PROJECT_KEYS}
        cc_row.update({"cost_center": cost_center, "projects": cc_projects})
        cost_centers.append(cc_row)

    ret = {key: sum(row[key] for row in cost_centers) for key in PROJECT_KEYS}
    ret["cost_centers"] = cost_centers
    return ret


def labor_costs_by_user(date_range, *, project=None, cost_center=None):
    if project is not None:
        projects = _labor_costs_by_project_id(
            date_range, where=["p.id=%s"], params=[project]
        )
    elif cost_center is not None:
        projects = _labor_costs_by_project_id(
            date_range, where=["p.cost_center_id=%s"], params=[cost_center]
        )
    else:
        projects = _labor_costs_by_project_id(date_range)

    users = User.objects.filter(
        id__in=set(
            chain.from_iterable(row["by_user"].keys() for row in projects.values())
        )
    )
    by_user = defaultdict(lambda: dict.fromkeys(USER_KEYS, Z))
    overall = dict.fromkeys(PROJECT_KEYS, Z)

    for row in projects.values():
        for key in PROJECT_KEYS:
            overall[key] += row[key]
        for key in USER_KEYS:
            for user in users:
                by_user[user][key] += row["by_user"][user.id][key]

    return {"by_user": [{"user": user, **by_user[user]} for user in users], **overall}


def test():  # pragma: no cover
    from pprint import pprint
    import datetime as dt

    # pprint(labor_costs_by_cost_center([dt.date(2019, 1, 1), dt.date.today()]))
    pprint(labor_costs_by_user([dt.date(2020, 1, 1), dt.date.today()], cost_center=1))
