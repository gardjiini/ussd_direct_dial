from django.urls import path
from . import views

urlpatterns = [
    path('ussd/', views.ussd_view, name = 'ussd_view'),
]