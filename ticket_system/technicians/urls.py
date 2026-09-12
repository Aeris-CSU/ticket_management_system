from django.urls import path
from .views import TechnicianRegister, TechnicianLogin, TechnicianView
urlpatterns = [
    path('technicians/create/', TechnicianRegister.as_view()),
    path('login/', TechnicianLogin.as_view()),
    path('technicians/', TechnicianView.as_view()),
]