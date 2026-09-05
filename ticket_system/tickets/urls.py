from django.urls import path
from .views import *

urlpatterns = [
    path('tickets/', TicketsView.as_view()),
]