from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import Authentication
from customers.models import Customers


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AuthenticationApiTests(APITestCase):
    def setUp(self):
        self.admin = Authentication.objects.create_user(username='admin', password='AdminPass123!x', role='ADMIN')

    def test_public_registration_creates_customer_only(self):
        response = self.client.post('/api/register/', {
            'username': 'newcustomer', 'password': 'CustomerPass123!x', 'address': 'School',
            'role': 'ADMIN', 'is_superuser': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = Authentication.objects.get(username='newcustomer')
        self.assertEqual(user.role, Authentication.ROLE_CHOICES.CUSTOMER)
        self.assertTrue(Customers.objects.filter(user=user).exists())
        self.assertNotIn('password', response.data)

    def test_public_technician_registration_is_blocked(self):
        response = self.client.post('/api/register-technicians/', {
            'username': 'tech', 'password': 'TechnicianPass123!x',
            'specialization': 'Networks', 'availability_status': 'AVAILABLE',
        }, format='json')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertFalse(Authentication.objects.filter(username='tech').exists())

    def test_admin_can_create_technician_and_public_user_cannot_set_role(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/register-technicians/', {
            'username': 'tech', 'password': 'TechnicianPass123!x',
            'specialization': 'Networks', 'availability_status': 'AVAILABLE',
            'role': 'ADMIN', 'is_superuser': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = Authentication.objects.get(username='tech')
        self.assertEqual(user.role, Authentication.ROLE_CHOICES.TECHNICIAN)
        self.assertFalse(user.is_superuser)
        self.assertNotIn('password', response.data)

    def test_login_access_and_refresh_tokens(self):
        Authentication.objects.create_user(username='customer', password='CustomerPass123!x', role='CUSTOMER')
        login = self.client.post('/api/login/', {'username': 'customer', 'password': 'CustomerPass123!x'}, format='json')
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertEqual(login.data['account']['role'], 'CUSTOMER')
        self.assertNotIn('password', login.data['account'])

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['tokens']['access']}")
        self.assertEqual(self.client.get('/api/accounts/').status_code, status.HTTP_200_OK)
        refreshed = self.client.post('/api/token/refresh/', {'refresh': login.data['tokens']['refresh']}, format='json')
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertIn('access', refreshed.data)

    def test_invalid_login_is_rejected(self):
        response = self.client.post('/api/login/', {
            'username': 'admin', 'password': 'incorrect-password',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_accounts_are_role_restricted(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all('password' not in account for account in response.data))

    def test_vite_preflight_allows_bearer_json_requests(self):
        for origin in ('http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:5174', 'http://127.0.0.1:5174'):
            with self.subTest(origin=origin):
                response = self.client.options(
                    '/api/tickets/',
                    HTTP_ORIGIN=origin,
                    HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET',
                    HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization,content-type',
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response['Access-Control-Allow-Origin'], origin)
                self.assertIn('Authorization', response['Access-Control-Allow-Headers'])

        rejected = self.client.options(
            '/api/tickets/',
            HTTP_ORIGIN='https://untrusted.example',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET',
        )
        self.assertNotIn('Access-Control-Allow-Origin', rejected)

    def test_protected_endpoints_reject_unauthenticated_and_invalid_jwt_requests(self):
        for path in ('/api/tickets/', '/api/assignments/', '/api/customers/', '/api/technicians/', '/api/accounts/'):
            with self.subTest(path=path):
                self.client.credentials()
                self.assertEqual(self.client.get(path).status_code, status.HTTP_401_UNAUTHORIZED)
                self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
                self.assertEqual(self.client.get(path).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_weak_password_change_returns_json_validation_error(self):
        customer = Authentication.objects.create_user(username='customer', password='CustomerPass123!x', role='CUSTOMER')
        profile = Customers.objects.create(user=customer, address='School')
        self.client.force_authenticate(customer)
        response = self.client.put(f'/api/customers/{profile.pk}/', {'password': 'weak'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        customer.refresh_from_db()
        self.assertTrue(customer.check_password('CustomerPass123!x'))
