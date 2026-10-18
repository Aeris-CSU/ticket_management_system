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
            'contact_number': '09171234567',
            'role': 'ADMIN', 'is_superuser': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = Authentication.objects.get(username='newcustomer')
        self.assertEqual(user.role, Authentication.ROLE_CHOICES.CUSTOMER)
        self.assertTrue(Customers.objects.filter(user=user).exists())
        self.assertNotIn('password', response.data)
        self.assertEqual(Customers.objects.get(user=user).contact_number, '09171234567')

    def test_registration_requires_contact_number(self):
        for contact in (None, '', '   '):
            data = {'username': 'missingcontact', 'password': 'CustomerPass123!x', 'address': 'School'}
            if contact is not None:
                data['contact_number'] = contact
            response = self.client.post('/api/register/', data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertIn('contact_number', response.data)
        self.assertFalse(Authentication.objects.filter(username='missingcontact').exists())

    def test_admin_changes_password_and_old_password_stops_working(self):
        old_login = self.client.post('/api/login/', {'username': 'admin', 'password': 'AdminPass123!x'}).data
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/change-password/', {
            'current_password': 'AdminPass123!x',
            'new_password': 'FreshAdminSecret123!', 'confirm_password': 'FreshAdminSecret123!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('FreshAdminSecret123!'))
        self.assertNotEqual(self.admin.password, 'FreshAdminSecret123!')
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {old_login['tokens']['access']}")
        self.assertEqual(self.client.get('/api/accounts/').status_code, 401)
        self.client.credentials()
        self.assertEqual(self.client.post('/api/login/', {'username': 'admin', 'password': 'AdminPass123!x'}).status_code, 401)
        self.assertEqual(self.client.post('/api/login/', {'username': 'admin', 'password': 'FreshAdminSecret123!'}).status_code, 200)

    def test_password_change_rejects_invalid_inputs_and_other_roles(self):
        self.client.force_authenticate(self.admin)
        for current, new, confirmation in [
            ('wrong', 'FreshAdminSecret123!', 'FreshAdminSecret123!'),
            ('AdminPass123!x', 'FreshAdminSecret123!', 'different'),
            ('AdminPass123!x', 'weak', 'weak'),
        ]:
            response = self.client.post('/api/change-password/', {'current_password': current, 'new_password': new, 'confirm_password': confirmation})
            self.assertEqual(response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('AdminPass123!x'))
        customer = Authentication.objects.create_user(username='notadmin', password='CustomerPass123!', role='CUSTOMER')
        self.client.force_authenticate(customer)
        self.assertEqual(self.client.post('/api/change-password/', {}).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post('/api/change-password/', {}).status_code, 401)

    def test_seed_admin_does_not_overwrite_a_changed_password(self):
        from importlib import import_module
        from django.apps import apps
        from django.db import connection
        seed = import_module('authentication.migrations.0002_local_admin').create_local_admin
        with connection.schema_editor(atomic=False) as editor:
            seed(apps, editor)
            user = Authentication.objects.get(username='localadmin')
            self.assertEqual(user.role, 'ADMIN')
            user.set_password('ChangedLocalSecret123!')
            user.save()
            seed(apps, editor)
        user.refresh_from_db()
        self.assertTrue(user.check_password('ChangedLocalSecret123!'))

    def test_customer_contact_number_registration_update_and_list(self):
        response = self.client.post('/api/register/', {
            'username': 'contactcustomer', 'password': 'CustomerPass123!x',
            'address': 'School', 'contact_number': '+63 917 123 4567',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        customer = Customers.objects.get(user__username='contactcustomer')
        self.assertEqual(customer.contact_number, '+63 917 123 4567')
        self.client.force_authenticate(user=customer.user)
        response = self.client.put(f'/api/customers/{customer.pk}/', {
            'contact_number': '09171234568',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        customer.refresh_from_db()
        self.assertEqual(customer.contact_number, '09171234568')
        response = self.client.get('/api/customers/')
        self.assertEqual(response.data[0]['contact_number'], '09171234568')

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


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SelfDeletionTests(APITestCase):
    def test_customer_and_technician_can_only_delete_themselves(self):
        from technicians.models import Technicians
        for role in ('CUSTOMER', 'TECHNICIAN'):
            user = Authentication.objects.create_user(username=role, role=role)
            other = Authentication.objects.create_user(username=role + '-other', role=role)
            model = Customers if role == 'CUSTOMER' else Technicians
            profile = model.objects.create(user=user)
            self.client.force_authenticate(user)
            response = self.client.delete('/api/accounts/me/', {'id': other.pk}, format='json')
            self.assertEqual(response.status_code, 204)
            self.assertFalse(Authentication.objects.filter(pk=user.pk).exists())
            self.assertFalse(model.objects.filter(pk=profile.pk).exists())
            self.assertTrue(Authentication.objects.filter(pk=other.pk).exists())

    def test_admin_and_anonymous_cannot_self_delete(self):
        self.assertIn(self.client.delete('/api/accounts/me/').status_code, (401, 403))
        admin = Authentication.objects.create_user(username='admin-self', role='ADMIN')
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.delete('/api/accounts/me/').status_code, 403)
        self.assertTrue(Authentication.objects.filter(pk=admin.pk).exists())

    def test_history_blocks_self_deletion(self):
        from tickets.models import Tickets
        from technicians.models import Technicians
        from assignments.models import Assignments
        customer_user = Authentication.objects.create_user(username='customer-self', role='CUSTOMER')
        customer = Customers.objects.create(user=customer_user)
        ticket = Tickets.objects.create(customer=customer, problem_title='Issue', problem_description='Help')
        tech_user = Authentication.objects.create_user(username='tech-self', role='TECHNICIAN')
        tech = Technicians.objects.create(user=tech_user, specialization='IT')
        Assignments.objects.create(tickets=ticket, technicians=tech, is_active=False)
        for user in (customer_user, tech_user):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.delete('/api/accounts/me/').status_code, 409)
            self.assertTrue(Authentication.objects.filter(pk=user.pk).exists())
