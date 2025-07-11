"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = 'authentication'

urlpatterns = [
    path(r'login/', LoginView.as_view(), name='login'),
    path(r'logout/', LogoutView.as_view(), name='logout'),
    path(r'whoami/', WhoAmIView.as_view(), name='whoami'),
]
