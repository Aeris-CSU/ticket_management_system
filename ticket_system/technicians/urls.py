from django.urls import path
from .views import TechnicianRegister, TechnicianLogin, TechnicianView
urlpatterns = [
    path('technician/create/', TechnicianRegister.as_view()),
    path('login/', TechnicianLogin.as_view()),
    path('accounts/', TechnicianView.as_view()),
]