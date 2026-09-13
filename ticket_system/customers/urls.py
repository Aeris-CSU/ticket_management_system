from django.urls import path
from .views import *

urlpatterns = [
    path('customers/', CustomersView.as_view()),
    path('register-customers/', CustomersCreate.as_view()),
    path('customers/update/<int:pk>/', CustomersUpdate.as_view()),
    path('customers/delete/<int:pk>/', CustomersDelete.as_view()),
]
