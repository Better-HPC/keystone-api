"""URL routing for the parent application."""

from django.urls import path

from .views import *

app_name = 'authentication'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('whoami/', WhoAmIView.as_view(), name='whoami'),
]
