from django.urls import path
from .views import *

urlpatterns = [
    path('assignments/history/', TechnicianHistory.as_view()),
    path('assignments/history/<int:pk>/', TechnicianHistory.as_view()),
    path('assignments/', AssignmentsView.as_view()),
    path('assignments/create/', AssignmentCreateView.as_view()),
    path('assignments/update/<int:pk>/', AssignmentUpdate.as_view()),
    path('assignments/delete/<int:pk>/', AssignmentDelete.as_view()),
    path('assignments/<int:pk>/', AssignmentsDetail.as_view()),

]
