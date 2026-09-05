from django.urls import path
from .views import *

urlpatterns = [
    path('assignments/', AssignmentsView.as_view()),
]