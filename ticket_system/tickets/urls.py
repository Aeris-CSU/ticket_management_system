from django.urls import path
from .views import *

urlpatterns = [
    path('tickets/', TicketsView.as_view()),
    path('tickets/create/', TicketsCreate.as_view()),
]