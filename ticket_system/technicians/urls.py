from django.urls import path
from .views import TechnicianRegister, TechnicianLogin, TechnicianView
urlpatterns = [
    path('register/', TechnicianRegister.as_view()),
    path('login/', TechnicianLogin.as_view()),
    path('accounts/', TechnicianView.as_view()),
]