from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import Authentication
from technicians.models import Technicians


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TechnicianRegistrationTests(APITestCase):
    def setUp(self):
        self.admin = Authentication.objects.create_user(
            username='admin', password='AdminPass123!x', role=Authentication.ROLE_CHOICES.ADMIN,
        )

    def test_admin_creates_technician_using_model_default_availability(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/register-technicians/', {
            'username': 'tech-new',
            'password': 'TechnicianPass123!x',
            'first_name': 'Taylor',
            'last_name': 'Reed',
            'email': 'taylor@example.test',
            'specialization': 'Hardware support',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        account = Authentication.objects.get(username='tech-new')
        technician = Technicians.objects.get(user=account)
        self.assertEqual(account.role, Authentication.ROLE_CHOICES.TECHNICIAN)
        self.assertTrue(account.check_password('TechnicianPass123!x'))
        self.assertEqual(account.first_name, 'Taylor')
        self.assertEqual(technician.specialization, 'Hardware support')
        self.assertEqual(technician.availability_status, Technicians.Availability.AVAILABLE)
        self.assertNotIn('password', response.data)

    def test_non_admin_cannot_register_a_technician(self):
        customer = Authentication.objects.create_user(
            username='customer', password='CustomerPass123!x', role=Authentication.ROLE_CHOICES.CUSTOMER,
        )
        self.client.force_authenticate(customer)
        response = self.client.post('/api/register-technicians/', {
            'username': 'tech-denied',
            'password': 'TechnicianPass123!x',
            'specialization': 'Hardware support',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Authentication.objects.filter(username='tech-denied').exists())
