import datetime as dt
import operator
from collections import OrderedDict
from decimal import Decimal
from functools import reduce
from itertools import count

from django import forms
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.html import strip_tags
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from workbench import generic
from workbench.expenses.models import ExchangeRates, ExpenseReport
from workbench.tools.formats import Z2, currency, local_date_format
from workbench.tools.pdf import MarkupParagraph, mm, pdf_response


class ExpenseReportPDFView(generic.DetailView):
    model = ExpenseReport

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.closed_on:
            messages.warning(
                request,
                _(
                    "Please close the expense report first. Generating PDFs"
                    " for open expense reports isn't allowed."
                ),
            )
            return redirect(self.object)

        pdf, response = pdf_response(
            self.object.code,
            as_attachment=request.GET.get("disposition") == "attachment",
        )
        pdf.init_report()
        pdf.h1(_("expense report"))
        pdf.spacer(2 * mm)
        pdf.table(
            [
                (capfirst(_("of")), self.object.owned_by.get_full_name()),
                (capfirst(_("created at")), local_date_format(self.object.created_at)),
                (capfirst(_("status")), capfirst(self.object.pretty_status)),
            ],
            pdf.style.tableColumnsLeft,
            pdf.style.table,
        )
        pdf.spacer(5 * mm)

        counter = count(1)
        expenses = OrderedDict()
        for cost in self.object.expenses.select_related(
            "service__project__owned_by"
        ).order_by("rendered_on", "pk"):
            expenses.setdefault(cost.expense_currency, []).append(cost)

        for currency_code, sublist in sorted(expenses.items()):
            pdf.table(
                [(_("receipt"), "", "")]
                + [
                    (
                        "%d." % (next(counter),),
                        MarkupParagraph(
                            f"{local_date_format(cost.rendered_on)}<br />{cost.service.project}: {cost.service}<br />{cost.description}<br />&nbsp;",
                            pdf.style.normal,
                        ),
                        currency(cost.third_party_costs)
                        if cost.expense_cost is None
                        else currency(cost.expense_cost),
                    )
                    for cost in sublist
                ],
                (10 * mm, pdf.bounds.E - pdf.bounds.W - 10 * mm - 16 * mm, 16 * mm),
                pdf.style.tableHead,
            )

            pdf.spacer(0.7 * mm)
            total_cost = reduce(
                operator.add,
                (cost.expense_cost or cost.third_party_costs for cost in sublist),
                Z2,
            )
            pdf.table(
                [
                    (
                        "{} {}".format(
                            capfirst(_("total")),
                            currency_code or settings.WORKBENCH.CURRENCY,
                        ),
                        currency(total_cost),
                    )
                ],
                pdf.style.tableColumns,
                pdf.style.tableHeadLine,
            )
            pdf.spacer()

        pdf.generate()

        return response


class ConvertForm(forms.Form):
    day = forms.DateField()
    currency = forms.CharField()
    cost = forms.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        data = super().clean()
        if (day := data.get("day")) and day > dt.date.today():
            self.add_error("__all__", _("Crystal ball missing, sorry."))
        return data


def convert(request):
    form = ConvertForm(request.GET)
    if not form.is_valid():
        try:
            error = strip_tags(str(form.errors["__all__"]))
        except Exception:
            error = _("Failure while determining the exchange rate.")
        return JsonResponse({"cost": "", "error": error})
    try:
        rates = ExchangeRates.objects.for_day(form.cleaned_data["day"])
    except Exception as exc:
        # Request timeout, response format not JSON, etc...
        return JsonResponse({
            "cost": "",
            "error": "%s: %s"
            % (
                _("Failure while determining the exchange rate."),
                exc,
            ),
        })

    cost = form.cleaned_data["cost"] / Decimal(
        str(rates.rates["rates"][form.cleaned_data["currency"]])
    )
    return JsonResponse({"cost": cost.quantize(Z2)})
