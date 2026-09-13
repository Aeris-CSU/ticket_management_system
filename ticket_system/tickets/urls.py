from django.urls import path
from .views import *

urlpatterns = [
    path('tickets/', TicketsView.as_view()),
    path('tickets/create/', TicketsCreate.as_view()),
    path('tickets/update/<int:pk>/', TicketsUpdate.as_view()),
    path('tickets/delete/<int:pk>/', TicketsDelete.as_view()),
]