from django.urls import path
from .views import (
    Login,
    AdminRegister,
    AdminList,
    AccountList,
    SendOTPView,
    VerifyOTPAndRegisterCustomerView,
    VerifyOTPAndResetPasswordView,
    NotificationListView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
)

urlpatterns = [
    path('login/', Login.as_view(), name='login'),
    path('register/', AdminRegister.as_view(), name='register-admin'),
    path('admins/', AdminList.as_view(), name='admins-list'),
    path('accounts/', AccountList.as_view(), name='accounts-list'),

    # OTP Endpoints
    path('otp/send/', SendOTPView.as_view(), name='send-otp'),
    path('otp/register-customer/', VerifyOTPAndRegisterCustomerView.as_view(), name='otp-register-customer'),
    path('otp/reset-password/', VerifyOTPAndResetPasswordView.as_view(), name='otp-reset-password'),

    # Notification Endpoints
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('notifications/mark-all-read/', MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
]