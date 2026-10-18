from django.test import override_settings
from rest_framework.test import APITestCase
from authentication.models import Authentication
from customers.models import Customers


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CustomerProfileTests(APITestCase):
    def setUp(self):
        self.user = Authentication.objects.create_user(username='owner', password='secret', role='CUSTOMER')
        self.customer = Customers.objects.create(user=self.user, address='Old address')
        other = Authentication.objects.create_user(username='other', role='CUSTOMER')
        self.other = Customers.objects.create(user=other, address='Other address')
        self.client.force_authenticate(self.user)

    def test_customer_updates_own_information(self):
        response = self.client.put(f'/api/customers/{self.customer.pk}/', {
            'username': 'newname', 'first_name': 'Casey', 'last_name': '', 'email': '',
            'address': 'New address', 'contact_number': '09123456789', 'role': 'ADMIN',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.customer.refresh_from_db()
        self.assertEqual(self.user.username, 'newname')
        self.assertEqual(self.user.first_name, 'Casey')
        self.assertEqual(self.user.role, 'CUSTOMER')
        self.assertEqual(self.customer.address, 'New address')
        self.assertTrue(self.user.check_password('secret'))

    def test_cannot_edit_another_customer_on_either_route(self):
        for prefix in ('/api/customers/', '/api/customers/update/'):
            self.assertEqual(self.client.put(f'{prefix}{self.other.pk}/', {'address': 'Changed'}, format='json').status_code, 403)
        self.other.refresh_from_db()
        self.assertEqual(self.other.address, 'Other address')
        self.assertEqual([row['id'] for row in self.client.get('/api/customers/').data], [self.customer.pk])

    def test_duplicate_username_is_rejected(self):
        response = self.client.put(f'/api/customers/{self.customer.pk}/', {'username': 'other'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'owner')

    def test_admin_deletes_customer_profile_and_login_on_both_routes(self):
        admin = Authentication.objects.create_user(username='admin', role='ADMIN')
        self.client.force_authenticate(admin)
        for prefix in ('/api/customers/', '/api/customers/delete/'):
            user = Authentication.objects.create_user(username='delete-customer', role='CUSTOMER')
            customer = Customers.objects.create(user=user, address='Home')
            self.assertEqual(self.client.delete(f'{prefix}{customer.pk}/').status_code, 204)
            self.assertFalse(Customers.objects.filter(pk=customer.pk).exists())
            self.assertFalse(Authentication.objects.filter(pk=user.pk).exists())

    def test_customer_cannot_delete_any_account(self):
        for customer in (self.customer, self.other):
            for prefix in ('/api/customers/', '/api/customers/delete/'):
                self.assertEqual(self.client.delete(f'{prefix}{customer.pk}/').status_code, 403)
        self.assertTrue(Customers.objects.filter(pk=self.customer.pk).exists())

    def test_ticket_history_protects_customer_account(self):
        from tickets.models import Tickets
        Tickets.objects.create(customer=self.customer, problem_title='Help', problem_description='Issue')
        admin = Authentication.objects.create_user(username='admin', role='ADMIN')
        self.client.force_authenticate(admin)
        for prefix in ('/api/customers/', '/api/customers/delete/'):
            self.assertEqual(self.client.delete(f'{prefix}{self.customer.pk}/').status_code, 409)
        self.assertTrue(Customers.objects.filter(pk=self.customer.pk).exists())
        self.assertTrue(Authentication.objects.filter(pk=self.user.pk).exists())
