from django.urls import path
from .views import *

urlpatterns = [
    path('tickets/', TicketsView.as_view()),
    path('tickets/new/', TicketsCreate.as_view()),
]