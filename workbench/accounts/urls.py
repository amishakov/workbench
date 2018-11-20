from django.conf.urls import url

from . import views


urlpatterns = [
    url(r"^$", views.accounts, name="accounts"),
    url(r"^update/$", views.UserUpdateView.as_view(), name="accounts_update"),
    url(r"^login/$", views.login, name="login"),
    url(r"^oauth2/$", views.oauth2, name="accounts_oauth2"),
    url(r"^logout/$", views.logout, name="logout"),
]
