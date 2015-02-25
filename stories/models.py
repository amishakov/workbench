from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from accounts.models import User
from projects.models import Project, Release
from services.models import ServiceType
from tools.urls import model_urls


@model_urls()
class Story(models.Model):
    UNSCHEDULED = 10
    SCHEDULED = 20
    STARTED = 30
    FINISHED = 40
    DELIVERED = 50
    ACCEPTED = 60
    REJECTED = 15

    STATUS_CHOICES = (
        (UNSCHEDULED, _('unscheduled')),
        (SCHEDULED, _('scheduled')),
        (STARTED, _('started')),
        (FINISHED, _('finished')),
        (DELIVERED, _('delivered')),
        (ACCEPTED, _('accepted')),
        (REJECTED, _('rejected')),
    )

    created_at = models.DateTimeField(
        _('created at'),
        default=timezone.now)
    requested_by = models.ForeignKey(
        User,
        verbose_name=_('requested by'))
    owned_by = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_('owned by'),
        related_name='owned_stories')
    title = models.CharField(
        _('title'),
        max_length=200)
    description = models.TextField(
        _('description'),
        blank=True)

    project = models.ForeignKey(
        Project,
        verbose_name=_('project'),
        related_name='stories')
    release = models.ForeignKey(
        Release,
        verbose_name=_('release'),
        related_name='stories',
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    status = models.PositiveIntegerField(
        _('status'),
        choices=STATUS_CHOICES,
        default=UNSCHEDULED)
    accepted_at = models.DateTimeField(
        _('accepted at'),
        blank=True,
        null=True)

    due_on = models.DateField(
        _('due on'),
        blank=True,
        null=True,
        help_text=_('This field should be left empty most of the time.'))

    position = models.PositiveIntegerField(_('position'), default=0)

    class Meta:
        ordering = ('position', 'id')
        verbose_name = _('story')
        verbose_name_plural = _('stories')

    def __str__(self):
        return self.title


class RequiredService(models.Model):
    story = models.ForeignKey(
        Story,
        verbose_name=_('story'),
        related_name='requiredservices',
    )
    service_type = models.ForeignKey(
        ServiceType,
        verbose_name=_('service type'),
        related_name='+',
    )
    estimated_effort = models.DecimalField(
        _('estimated effort'),
        max_digits=5,
        decimal_places=2,
        help_text=_('The original estimate.'))
    offered_effort = models.DecimalField(
        _('offered effort'),
        max_digits=5,
        decimal_places=2,
        help_text=_('Effort offered to the customer.'))
    planning_effort = models.DecimalField(
        _('planning effort'),
        max_digits=5,
        decimal_places=2,
        help_text=_(
            'Effort for planning. This value should reflect the current '
            ' state of affairs also when work is already in progress.'))

    class Meta:
        ordering = ('service_type',)
        unique_together = (('story', 'service_type'),)
        verbose_name = _('required service')
        verbose_name_plural = _('required services')

    def __str__(self):
        return '%s' % self.service_type

    @property
    def urls(self):
        return self.story.urls

    def get_absolute_url(self):
        return self.story.get_absolute_url()
