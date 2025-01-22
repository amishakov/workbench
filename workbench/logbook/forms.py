import datetime as dt

from django import forms
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import mark_safe
from django.utils.text import capfirst
from django.utils.timezone import localtime
from django.utils.translation import gettext, gettext_lazy as _, override

from workbench.accounts.features import FEATURES
from workbench.accounts.models import User
from workbench.contacts.models import Organization
from workbench.expenses.models import ExchangeRates
from workbench.logbook.models import Break, LoggedCost, LoggedHours
from workbench.offers.models import Offer
from workbench.projects.models import Campaign, InternalType, Project, Service
from workbench.services.models import ServiceType
from workbench.timer.models import Timestamp
from workbench.tools.forms import (
    Autocomplete,
    DateInput,
    Form,
    ModelForm,
    Textarea,
    add_prefix,
    querystring,
)
from workbench.tools.validation import (
    in_days,
    is_title_specific,
    logbook_lock,
    raise_if_errors,
)
from workbench.tools.xlsx import WorkbenchXLSXDocument


class DetectedTimestampForm(forms.Form):
    detected_ends_at = forms.CharField()

    def clean_detected_ends_at(self):
        value = parse_datetime(self.cleaned_data.get("detected_ends_at"))
        if not value:
            raise forms.ValidationError("Invalid value '%s'" % value)
        return value

    def build_if_valid(self, **kwargs):
        if self.is_valid():
            kwargs.setdefault("notes", gettext("<detected>"))
            return Timestamp(
                type=Timestamp.STOP,
                created_at=self.cleaned_data["detected_ends_at"],
                **kwargs,
            )
        return None


class LoggedHoursSearchForm(Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Search")}
        ),
        label="",
    )
    rendered_by = forms.TypedChoiceField(
        coerce=int,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="",
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        widget=Autocomplete(model=Project),
        label="",
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        widget=Autocomplete(model=Organization),
        label="",
    )
    date_from = forms.DateField(widget=DateInput, required=False, label="")
    date_until = forms.DateField(
        widget=DateInput, required=False, label=mark_safe("&ndash;&nbsp;")
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        required=False,
        widget=forms.HiddenInput,
        label="",
    )
    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.all(),
        required=False,
        widget=forms.HiddenInput,
        label="",
    )
    offer = forms.IntegerField(required=False, widget=forms.HiddenInput, label="")
    not_archived = forms.BooleanField(
        required=False, widget=forms.HiddenInput, label=""
    )
    internal_type = forms.IntegerField(
        required=False, widget=forms.HiddenInput, label=""
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rendered_by"].choices = User.objects.choices(
            collapse_inactive=False, myself=True
        )

    def filter(self, queryset):
        data = self.cleaned_data
        queryset = queryset.search(data.get("q"))
        if data.get("rendered_by") == -1:
            queryset = queryset.filter(rendered_by=self.request.user)
        elif data.get("rendered_by"):
            queryset = queryset.filter(rendered_by=data.get("rendered_by"))
        if data.get("project"):
            queryset = queryset.filter(service__project=data.get("project"))
        if data.get("organization"):
            queryset = queryset.filter(
                service__project__customer=data.get("organization")
            )
        if data.get("date_from"):
            queryset = queryset.filter(rendered_on__gte=data.get("date_from"))
        if data.get("date_until"):
            queryset = queryset.filter(rendered_on__lte=data.get("date_until"))

        # "hidden" filters
        self.hidden_filters = []
        if data.get("service"):
            service = data.get("service")
            self.hidden_filters.append(
                (
                    f"{capfirst(service._meta.verbose_name)}: {service}",
                    querystring(self.request.GET, service=""),
                ),
            )
            queryset = queryset.filter(service=service)
        if data.get("campaign"):
            campaign = data.get("campaign")
            self.hidden_filters.append(
                (
                    f"{capfirst(campaign._meta.verbose_name)}: {campaign}",
                    querystring(self.request.GET, campaign=""),
                ),
            )
            queryset = queryset.filter(service__project__campaign=campaign)
        if data.get("offer") == 0:
            self.hidden_filters.append((
                _("No offer"),
                querystring(self.request.GET, offer=""),
            ))
            queryset = queryset.filter(service__offer__isnull=True)
        elif data.get("offer"):
            offer = Offer.objects.filter(pk=data.get("offer")).first()
            self.hidden_filters.append(
                (
                    f"{capfirst(Offer._meta.verbose_name)}: {offer}",
                    querystring(self.request.GET, offer=""),
                ),
            )
            queryset = queryset.filter(service__offer=offer)
        if data.get("not_archived"):
            self.hidden_filters.append((
                _("Not archived"),
                querystring(self.request.GET, not_archived=""),
            ))
            queryset = queryset.filter(archived_at__isnull=True)
        if data.get("internal_type") == -1:
            self.hidden_filters.append((
                _("External"),
                querystring(self.request.GET, internal_type=""),
            ))
            queryset = queryset.exclude(service__project__type=Project.INTERNAL)
        elif (pk := data.get("internal_type")) and (
            internal_type := InternalType.objects.filter(pk=pk).first()
        ):
            self.hidden_filters.append((
                f"{capfirst(internal_type._meta.verbose_name)}: {internal_type.name}",
                querystring(self.request.GET, internal_type=""),
            ))
            queryset = queryset.filter(service__project__internal_type=internal_type)

        return queryset.select_related("service__project__owned_by", "rendered_by")

    def response(self, request, queryset):
        if (
            request.GET.get("export") == "xlsx"
            and request.user.features[FEATURES.CONTROLLING]
        ):
            xlsx = WorkbenchXLSXDocument()
            xlsx.logged_hours(queryset)
            return xlsx.to_response("hours.xlsx")
        return None


class LoggedCostSearchForm(Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Search")}
        ),
        label="",
    )
    rendered_by = forms.TypedChoiceField(
        coerce=int,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="",
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        widget=Autocomplete(model=Project),
        label="",
    )
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        widget=Autocomplete(model=Organization),
        label="",
    )
    expenses = forms.BooleanField(required=False, label=_("expenses"))
    date_from = forms.DateField(widget=DateInput, required=False, label="")
    date_until = forms.DateField(
        widget=DateInput, required=False, label=mark_safe("&ndash;&nbsp;")
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        required=False,
        widget=forms.HiddenInput,
        label="",
    )
    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.all(),
        required=False,
        widget=forms.HiddenInput,
        label="",
    )
    offer = forms.IntegerField(required=False, widget=forms.HiddenInput, label="")
    not_archived = forms.BooleanField(
        required=False, widget=forms.HiddenInput, label=""
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rendered_by"].choices = User.objects.choices(
            collapse_inactive=False, myself=True
        )

        if not self.request.user.features[FEATURES.EXPENSES]:
            self.fields.pop("expenses")

    def filter(self, queryset):
        data = self.cleaned_data
        queryset = queryset.search(data.get("q"))
        if data.get("rendered_by") == -1:
            queryset = queryset.filter(rendered_by=self.request.user)
        elif data.get("rendered_by"):
            queryset = queryset.filter(rendered_by=data.get("rendered_by"))
        if data.get("project"):
            queryset = queryset.filter(service__project=data.get("project"))
        if data.get("organization"):
            queryset = queryset.filter(
                service__project__customer=data.get("organization")
            )
        if data.get("expenses"):
            queryset = queryset.filter(are_expenses=True)
        if data.get("date_from"):
            queryset = queryset.filter(rendered_on__gte=data.get("date_from"))
        if data.get("date_until"):
            queryset = queryset.filter(rendered_on__lte=data.get("date_until"))

        # "hidden" filters
        self.hidden_filters = []
        if data.get("service"):
            service = data.get("service")
            self.hidden_filters.append(
                (
                    f"{capfirst(service._meta.verbose_name)}: {service}",
                    querystring(self.request.GET, service=""),
                ),
            )
            queryset = queryset.filter(service=service)
        if data.get("campaign"):
            campaign = data.get("campaign")
            self.hidden_filters.append(
                (
                    f"{capfirst(campaign._meta.verbose_name)}: {campaign}",
                    querystring(self.request.GET, campaign=""),
                ),
            )
            queryset = queryset.filter(service__project__campaign=campaign)
        if data.get("offer") == 0:
            self.hidden_filters.append((
                _("No offer"),
                querystring(self.request.GET, offer=""),
            ))
            queryset = queryset.filter(service__offer__isnull=True)
        elif data.get("offer"):
            offer = Offer.objects.filter(pk=data.get("offer")).first()
            self.hidden_filters.append(
                (
                    f"{capfirst(Offer._meta.verbose_name)}: {offer}",
                    querystring(self.request.GET, offer=""),
                ),
            )
            queryset = queryset.filter(service__offer=offer)
        if data.get("not_archived"):
            self.hidden_filters.append((
                _("Not archived"),
                querystring(self.request.GET, not_archived=""),
            ))
            queryset = queryset.filter(archived_at__isnull=True)

        return queryset.select_related("service__project__owned_by", "rendered_by")

    def response(self, request, queryset):
        if (
            request.GET.get("export") == "xlsx"
            and request.user.features[FEATURES.CONTROLLING]
        ):
            xlsx = WorkbenchXLSXDocument()
            xlsx.logged_costs(queryset)
            return xlsx.to_response("costs.xlsx")
        return None


@add_prefix("modal")
class LoggedHoursForm(ModelForm):
    user_fields = default_to_current_user = ("rendered_by",)

    service_title = forms.CharField(label=_("title"), required=False, max_length=200)
    service_description = forms.CharField(
        label=_("description"), required=False, widget=Textarea({"rows": 2})
    )
    service_type = forms.ModelChoiceField(
        ServiceType.objects.all(), label=ServiceType._meta.verbose_name, required=False
    )

    class Meta:
        model = LoggedHours
        fields = ("rendered_by", "rendered_on", "service", "hours", "description")
        widgets = {"description": Textarea({"rows": 2})}

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        if self.project:
            initial = kwargs.setdefault("initial", {})
            request = kwargs["request"]

            if pk := request.GET.get("copy"):
                try:
                    hours = LoggedHours.objects.get(pk=pk)
                except (LoggedHours.DoesNotExist, TypeError, ValueError):
                    pass
                else:
                    initial.update({
                        "service": hours.service_id,
                        "rendered_on": hours.rendered_on.isoformat(),
                        "hours": hours.hours,
                        "description": hours.description,
                    })

            for field in ["description", "hours", "rendered_on", "service"]:
                if value := request.GET.get(field):
                    initial[field] = value

            if not initial.get("hours") and request.user.hours_since_latest <= 12:
                initial.setdefault("hours", request.user.hours_since_latest)

            if not initial.get("service"):
                latest_on_project = (
                    LoggedHours.objects.filter(
                        rendered_by=request.user, service__project=self.project
                    )
                    .order_by("-created_at")
                    .first()
                )
                if latest_on_project:
                    initial.setdefault("service", latest_on_project.service_id)

        else:
            self.project = kwargs["instance"].service.project

        super().__init__(*args, **kwargs)
        self.fields["service"].choices = self.project.services.logging().choices()
        self.fields["service"].required = False
        if len(self.fields["service"].choices) > 1 and not self.request.POST.get(
            "modal-service_title"
        ):
            self.hide_new_service = True
            self.fields["service"].widget.attrs["autofocus"] = True
        else:
            self.fields["service_title"].widget.attrs["autofocus"] = True

        if self.instance.pk:
            self.fields.pop("service_title")
            self.fields.pop("service_description")
            self.fields.pop("service_type")
            if (
                not self.instance.rendered_by.features[FEATURES.LATE_LOGGING]
                and self.instance.rendered_on < logbook_lock()
            ):
                self.fields["hours"].disabled = True
                self.fields["rendered_by"].disabled = True
                self.fields["rendered_on"].disabled = True

        else:
            if self.project.flat_rate is not None:
                self.fields.pop("service_type")

    def clean(self):
        data = super().clean()
        errors = {}
        if not data.get("service") and not data.get("service_title"):
            errors["service"] = _(
                "This field is required unless you create a new service."
            )
        elif data.get("service") and data.get("service_title"):
            errors["service"] = _(
                "Deselect the existing service if you want to create a new service."
            )
        if self.project.closed_on:
            if self.project.is_logbook_locked:
                errors["__all__"] = _("This project has been closed too long ago.")
            else:
                self.add_warning(
                    _("This project has been closed recently."), code="project-closed"
                )
        if self.instance.invoice_service:
            self.add_warning(
                _("This entry is already part of an invoice."), code="part-of-invoice"
            )
        if data.get("service_title") and not is_title_specific(data["service_title"]):
            self.add_warning(
                _(
                    "This title seems awfully unspecific."
                    " Please use specific titles for services."
                ),
                code="unspecific-service",
            )

        if all(
            f in self.fields and data.get(f) for f in ["rendered_by", "rendered_on"]
        ) and (not self.instance.pk or ("rendered_on" in self.changed_data)):
            if data["rendered_by"].features[FEATURES.LATE_LOGGING]:
                # Fine
                pass
            elif data["rendered_on"] < logbook_lock():
                errors["rendered_on"] = _("Hours have to be logged in the same week.")
            elif data["rendered_on"] > in_days(7):
                errors["rendered_on"] = _("That's too far in the future.")
            elif data["rendered_on"] > in_days(1):
                self.add_warning(
                    _(
                        "Logging (too) early is certainly better than logging (too) late, but are you sure this is correct?"
                    ),
                    code="maybe-too-early",
                )

            if data["rendered_by"].features[
                FEATURES.LATE_LOGGING_NAG
            ] and logbook_lock() <= data["rendered_on"] < in_days(-2):
                self.add_warning(
                    _(
                        "You are a bit late. Please try logging your hours immediately upon finishing work."
                    ),
                    code="you-are-late",
                )

        if (
            all(data.get(f) for f in ["rendered_by", "rendered_on", "hours"])
            and not self.instance.pk
        ):
            msg = data["rendered_by"].take_a_break_warning(
                day=data["rendered_on"], add=data["hours"]
            )
            if msg:
                self.add_warning(msg, code="take-a-break")

        try:
            latest = LoggedHours.objects.filter(
                Q(rendered_by=self.request.user), ~Q(id=self.instance.id)
            ).latest("pk")
        except LoggedHours.DoesNotExist:
            pass
        else:
            fields = ["rendered_by", "rendered_on", "service", "hours", "description"]
            for field in fields:
                if data.get(field) != getattr(latest, field):
                    break
            else:
                self.add_warning(
                    _("This seems to be a duplicate. Is it?"), code="maybe-duplicate"
                )

        raise_if_errors(errors)
        return data

    def save(self):
        instance = super().save(commit=False)
        timestamp = None
        if not instance.pk:
            instance.created_by = self.request.user
            if pk := self.request.GET.get("timestamp"):
                timestamp = Timestamp.objects.filter(
                    user=self.request.user, id=pk
                ).first()
            else:
                timestamp = DetectedTimestampForm(self.request.GET).build_if_valid(
                    user=self.request.user, logged_hours=instance
                )

        if not self.cleaned_data.get("service") and self.cleaned_data.get(
            "service_title"
        ):
            service = Service(
                project=self.project,
                title=self.cleaned_data["service_title"],
                description=self.cleaned_data["service_description"],
            )
            if self.project.flat_rate is not None:
                with override(settings.WORKBENCH.PDF_LANGUAGE):
                    service.effort_type = gettext("flat rate")
                    service.effort_rate = self.project.flat_rate
            elif service_type := self.cleaned_data.get("service_type"):
                service.effort_type = service_type.title
                service.effort_rate = service_type.hourly_rate
            service.save()
            instance.service = service
        instance.save()
        if timestamp:
            timestamp.logged_hours = instance
            timestamp.save()

        return instance


@add_prefix("modal")
class LoggedCostForm(ModelForm):
    user_fields = default_to_current_user = ("rendered_by",)

    class Meta:
        model = LoggedCost
        fields = (
            "service",
            "rendered_by",
            "rendered_on",
            "expense_currency",
            "expense_cost",
            "third_party_costs",
            "are_expenses",
            "cost",
            "description",
        )
        widgets = {"description": Textarea({"rows": 2})}

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project", None)
        if self.project:
            initial = kwargs.setdefault("initial", {})
            request = kwargs["request"]

            if pk := request.GET.get("copy"):
                try:
                    cost = LoggedCost.objects.get(pk=pk)
                except (LoggedHours.DoesNotExist, TypeError, ValueError):
                    pass
                else:
                    initial.update({
                        "service": cost.service_id,
                        "rendered_on": cost.rendered_on,
                        "expense_currency": cost.expense_currency,
                        "expense_cost": cost.expense_cost,
                        "third_party_costs": cost.third_party_costs,
                        "are_expenses": cost.are_expenses,
                        "cost": cost.cost,
                        "description": cost.description,
                    })

            elif service := request.GET.get("service"):
                initial.setdefault("service", service)

        else:
            self.project = kwargs["instance"].service.project

        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.instance.created_by = self.request.user

        self.fields["service"].choices = self.project.services.logging().choices()
        self.fields["cost"].help_text = mark_safe(
            "{} "
            '<a href="#" data-multiply-cost="1" class="">100%</a> '
            '<a href="#" data-multiply-cost="1.15" class="">115%</a> '
            "{}"
            "".format(
                _("Copy value from third party costs"), self.fields["cost"].help_text
            )
        )

        if self.instance.expense_report:
            self.fields["rendered_by"].disabled = True
            self.fields["rendered_on"].disabled = True
            self.fields["are_expenses"].disabled = True
            self.fields["third_party_costs"].disabled = True
            self.fields["expense_currency"].disabled = True
            self.fields["expense_cost"].disabled = True

        if self.request.user.features[FEATURES.FOREIGN_CURRENCIES]:
            rates = ExchangeRates.objects.newest()
            self.fields["expense_currency"] = forms.ChoiceField(
                choices=[("", "----------")]
                + [(currency, currency) for currency in rates.rates["rates"]],
                widget=forms.Select(attrs={"class": "form-select"}),
                required=False,
                initial=self.instance.expense_currency,
                label=self.instance._meta.get_field("expense_currency").verbose_name,
            )
        else:
            self.fields.pop("expense_currency")
            self.fields.pop("expense_cost")

        if not self.request.user.features[FEATURES.EXPENSES]:
            self.fields.pop("are_expenses")
            self.fields.pop("expense_currency", None)
            self.fields.pop("expense_cost", None)

    def clean(self):
        data = super().clean()
        errors = {}
        if self.project.closed_on:
            if self.project.closed_on < in_days(-14):
                errors["__all__"] = _("This project has been closed too long ago.")
            else:
                self.add_warning(
                    _("This project has been closed recently."), code="project-closed"
                )
        if self.instance.invoice_service:
            self.add_warning(
                _("This entry is already part of an invoice."), code="part-of-invoice"
            )
        if data.get("are_expenses") and not data.get("third_party_costs"):
            errors["third_party_costs"] = (
                _("Providing third party costs is necessary for expenses."),
            )
        if data.get("cost") and data.get("third_party_costs") is not None:
            if data["cost"] < data["third_party_costs"]:
                self.add_warning(
                    _("Third party costs shouldn't be higher than costs."),
                    code="third-party-costs-higher",
                )
        if data.get("rendered_on") and data["rendered_on"] > in_days(360):
            errors["rendered_on"] = _("That's too far in the future.")
        raise_if_errors(errors)
        return data


class BreakSearchForm(Form):
    user = forms.TypedChoiceField(
        coerce=int,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].choices = User.objects.choices(
            collapse_inactive=True, myself=True
        )

    def filter(self, queryset):
        # data = self.cleaned_data
        # queryset = queryset.search(data.get("q"))
        queryset = self.apply_owned_by(queryset, attribute="user")
        return queryset.select_related("user")

    def response(self, request, queryset):
        if (
            request.GET.get("export") == "xlsx"
            and request.user.features[FEATURES.CONTROLLING]
        ):
            xlsx = WorkbenchXLSXDocument()
            xlsx.table_from_queryset(queryset)
            return xlsx.to_response("breaks.xlsx")
        return None


@add_prefix("modal")
class BreakForm(ModelForm):
    day = forms.DateField(label=capfirst(_("day")))
    starts_at = forms.TimeField(label=capfirst(_("starts at")))
    ends_at = forms.TimeField(label=capfirst(_("ends at")))

    class Meta:
        model = Break
        fields = ["description"]
        widgets = {"description": Textarea({"rows": 2})}

    def __init__(self, *args, **kwargs):
        request = kwargs["request"]
        initial = kwargs.setdefault("initial", {})
        for field in ["day", "starts_at", "ends_at", "description"]:
            if value := request.GET.get(field):
                initial[field] = value

        if "instance" not in kwargs:
            if "starts_at" not in initial:
                latest = localtime(request.user.latest_created_at)
                if dt.date.today() == latest.date():
                    initial.setdefault("starts_at", latest.time())
            initial.setdefault("day", dt.date.today())
            initial.setdefault("ends_at", localtime(timezone.now()).time())

        else:
            initial.setdefault("day", kwargs["instance"].starts_at.date())
            initial.setdefault(
                "starts_at", localtime(kwargs["instance"].starts_at).time()
            )
            initial.setdefault("ends_at", localtime(kwargs["instance"].ends_at).time())

        super().__init__(*args, **kwargs)

        self.order_fields(("day", "starts_at", "ends_at"))

    def clean(self):
        data = super().clean()
        errors = {}
        if data.get("day"):
            if data["day"] < logbook_lock() - dt.timedelta(days=7):
                errors["day"] = _("Breaks have to be logged promptly.")
            elif data["day"] > in_days(7):
                errors["day"] = _("That's too far in the future.")

        raise_if_errors(errors)

        if all(data.get(f) for f in ("day", "starts_at", "ends_at")):
            data["starts_at"] = timezone.make_aware(
                dt.datetime.combine(data["day"], data["starts_at"])
            )
            data["ends_at"] = timezone.make_aware(
                dt.datetime.combine(data["day"], data["ends_at"])
            )

        return data

    def save(self):
        new = not self.instance.pk
        instance = super().save(commit=False)
        instance.starts_at = self.cleaned_data["starts_at"]
        instance.ends_at = self.cleaned_data["ends_at"]
        if new:
            instance.user = self.request.user
        instance.save()

        if not new:
            return instance

        timestamp = None
        if pk := self.request.GET.get("timestamp"):
            Timestamp.objects.filter(user=self.request.user, id=pk).update(
                logged_break=instance
            )
        else:
            timestamp = DetectedTimestampForm(self.request.GET).build_if_valid(
                user=self.request.user, logged_break=instance
            )

        if timestamp:
            timestamp.save()
        return instance


class LoggedMoveForm(ModelForm):
    service = forms.ModelChoiceField(
        queryset=Service.objects.logging().filter(project__closed_on__isnull=True),
        widget=Autocomplete(model=Service),
        label="",
        initial="",
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("initial", {}).setdefault("service", "")
        super().__init__(*args, **kwargs)

        if self.instance.archived_at:
            self.move_forbidden = _("Cannot move archived logbook entries.")
        elif self.instance.service.project.closed_on:
            self.move_forbidden = _("Cannot move logbook entries of closed projects.")
        else:
            self.move_forbidden = False
        if self.move_forbidden:
            messages.error(self.request, self.move_forbidden)

    def clean(self):
        data = super().clean()
        if self.move_forbidden:
            self.add_error("__all__", self.move_forbidden)
        return data


@add_prefix("modal")
class LoggedHoursMoveForm(LoggedMoveForm):
    class Meta:
        model = LoggedHours
        fields = ["service"]


@add_prefix("modal")
class LoggedCostMoveForm(LoggedMoveForm):
    class Meta:
        model = LoggedCost
        fields = ["service"]
