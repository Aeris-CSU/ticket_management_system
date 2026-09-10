from django.urls import path
from .views import CustomersView, CustomersCreate

urlpatterns = [
    path('customers/', CustomersView.as_view()),
    path('customers/create/', CustomersCreate.as_view()),
]
