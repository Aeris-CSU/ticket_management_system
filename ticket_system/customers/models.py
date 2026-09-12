from django.db import models
from django.conf import settings

class Customers(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=100)


#
#   username = validated_data['username'],
#             password = validated_data['password'],
#             role = Authentication.ROLE_CHOICES.CUSTOMER,
#             first_name = validated_data.get('first_name', ''),
#             last_name = validated_data.get('last_name', ''),
#             email = validated_data.get('email', ''),