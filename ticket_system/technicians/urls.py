from django.urls import path
from .views import *
urlpatterns = [
    path('register-technicians/', TechnicianRegister.as_view()),
    path('technicians/', TechnicianView.as_view()),
    path('technicians/update/<int:pk>', TechnicianUpdate.as_view()),
    path('technicians/delete/<int:pk>', TechnicianDelete.as_view()),
]