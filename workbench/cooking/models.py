from datetime import date, timedelta

from django.db import models
from django.utils.dates import WEEKDAYS
from django.utils.translation import ugettext_lazy as _

from workbench.accounts.models import User
from workbench.tools.models import Model
from workbench.tools.urls import model_urls


class DayQuerySet(models.QuerySet):
    def create_days(self):
        defaults = {
            default.day_of_week: default.user
            for default in DayOfWeekDefault.objects.all()
        }

        year = date.today().year + 1
        start = date(year, 1, 1)
        for offset in range(0, 366):
            day = start + timedelta(days=offset)
            if day.isoweekday() <= 5 and day.year == year:
                self.get_or_create(
                    day=day, defaults={"handled_by": defaults.get(day.isoweekday())}
                )


@model_urls()
class Day(Model):
    day = models.DateField(_("day"))
    handled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="+",
        blank=True,
        null=True,
        verbose_name=_("handled by"),
    )

    objects = DayQuerySet.as_manager()

    class Meta:
        ordering = ["day"]
        verbose_name = _("day")
        verbose_name_plural = _("days")

    def __str__(self):
        return "{} - {}".format(self.day, self.handled_by or "?")


@model_urls()
class Presence(Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="+", verbose_name=_("user")
    )
    year = models.IntegerField(_("year"))
    percentage = models.IntegerField(_("percentage"))

    class Meta:
        ordering = ["year"]
        unique_together = [("user", "year")]
        verbose_name = _("presence")
        verbose_name_plural = _("presences")

    def __str__(self):
        return "{}%".format(self.percentage)


class DayOfWeekDefault(Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="+", verbose_name=_("user")
    )
    day_of_week = models.IntegerField(
        _("day of week"), choices=sorted(WEEKDAYS.items()), unique=True
    )

    class Meta:
        ordering = ["day_of_week"]
        verbose_name = _("day of week default")
        verbose_name_plural = _("day of week defaults")

    def __str__(self):
        return self.get_day_of_week_display()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Day.objects.filter(
            day__week_day=(self.day_of_week + 1) % 7 + 1, handled_by=None
        ).update(handled_by=self.user)

    save.alters_data = True
