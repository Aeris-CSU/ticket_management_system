from django.db import models
from customers.models import Customers

# Create your models here.
class Tickets(models.Model):
    id = models.AutoField(primary_key=True)
    problem_title = models.CharField(max_length=200)
    problem_description = models.TextField()
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(Customers, on_delete=models.PROTECT)

