from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from accounts.models import User
from activities.models import Activity
from tools.forms import ModelForm


class ActivitySearchForm(forms.Form):
    owned_by = forms.TypedChoiceField(
        label=_('owned by'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owned_by'].choices = [
            ('', _('All users')),
            (0, _('Owned by inactive users')),
            (_('Active'), [
                (u.id, u.get_full_name())
                for u in User.objects.filter(is_active=True)
            ]),
        ]

    def filter(self, queryset):
        if not self.is_valid():
            return queryset

        data = self.cleaned_data
        if data.get('owned_by') == 0:
            queryset = queryset.filter(owned_by__is_active=False)
        elif data.get('owned_by'):
            queryset = queryset.filter(owned_by=data.get('owned_by'))

        return queryset


class ActivityForm(ModelForm):
    user_fields = default_to_current_user = ('owned_by',)

    is_completed = forms.BooleanField(
        label=_('is completed'),
        required=False,
    )

    class Meta:
        model = Activity
        fields = (
            'title', 'owned_by', 'due_on',
        )

    def save(self):
        instance = super().save(commit=False)
        if not instance.completed_at and self.cleaned_data.get('is_completed'):
            instance.completed_at = timezone.now()
        instance.save()
        return instance
