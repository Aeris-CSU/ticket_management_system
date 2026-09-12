from django.urls import path
from .views import *

urlpatterns = [
    path('login/', Login.as_view()),
    path('register/', AdminRegister.as_view()),
    path('admins/', AdminList.as_view()),
]