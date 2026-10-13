from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AccountList, AdminList

urlpatterns = [
    path('admins/', AdminList.as_view()),
    path('accounts/', AccountList.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
]
