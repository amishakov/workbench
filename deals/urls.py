from django.conf.urls import url

from deals.forms import DealSearchForm, DealForm
from deals.models import Deal
from tools.views import (
    ListView, DetailView, CreateView, UpdateView, DeleteView)


urlpatterns = [
    url(
        r'^$',
        ListView.as_view(
            model=Deal,
            search_form_class=DealSearchForm,
            select_related=('owned_by', 'stage'),
        ),
        name='deals_deal_list'),
    url(
        r'^(?P<pk>\d+)/$',
        DetailView.as_view(model=Deal),
        name='deals_deal_detail'),
    url(
        r'^create/$',
        CreateView.as_view(
            form_class=DealForm,
            model=Deal,
        ),
        name='deals_deal_create'),
    url(
        r'^(?P<pk>\d+)/update/$',
        UpdateView.as_view(
            form_class=DealForm,
            model=Deal,
        ),
        name='deals_deal_update'),
    url(
        r'^(?P<pk>\d+)/delete/$',
        DeleteView.as_view(model=Deal),
        name='deals_deal_delete'),
]
