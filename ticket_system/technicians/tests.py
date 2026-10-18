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

    def test_admin_deletes_profile_and_login_through_both_routes(self):
        self.client.force_authenticate(self.admin)
        for prefix in ('/api/technicians/', '/api/technicians/delete/'):
            user = Authentication.objects.create_user(username='delete-tech', password='secret', role='TECHNICIAN')
            tech = Technicians.objects.create(user=user, specialization='IT')
            response = self.client.delete(f'{prefix}{tech.pk}/')
            self.assertEqual(response.status_code, 204)
            self.assertFalse(Technicians.objects.filter(pk=tech.pk).exists())
            self.assertFalse(Authentication.objects.filter(pk=user.pk).exists())

    def test_non_admin_cannot_delete_technician(self):
        user = Authentication.objects.create_user(username='tech', password='secret', role='TECHNICIAN')
        tech = Technicians.objects.create(user=user, specialization='IT')
        self.client.force_authenticate(user)
        for prefix in ('/api/technicians/', '/api/technicians/delete/'):
            self.assertEqual(self.client.delete(f'{prefix}{tech.pk}/').status_code, 403)
        self.assertTrue(Authentication.objects.filter(pk=user.pk).exists())

    def test_assignment_history_prevents_account_deletion(self):
        from customers.models import Customers
        from tickets.models import Tickets
        from assignments.models import Assignments
        customer_user = Authentication.objects.create_user(username='owner', role='CUSTOMER')
        customer = Customers.objects.create(user=customer_user)
        user = Authentication.objects.create_user(username='historical-tech', role='TECHNICIAN')
        tech = Technicians.objects.create(user=user, specialization='IT')
        ticket = Tickets.objects.create(customer=customer, problem_title='Help', problem_description='Issue')
        Assignments.objects.create(tickets=ticket, technicians=tech, is_active=False)
        self.client.force_authenticate(self.admin)
        for prefix in ('/api/technicians/', '/api/technicians/delete/'):
            self.assertEqual(self.client.delete(f'{prefix}{tech.pk}/').status_code, 409)
        self.assertTrue(Authentication.objects.filter(pk=user.pk).exists())
        self.assertTrue(Technicians.objects.filter(pk=tech.pk).exists())

    def test_technician_edits_own_profile_and_cannot_edit_other_technicians(self):
        user = Authentication.objects.create_user(username='profile-tech', password='OldSecret123!', role='TECHNICIAN')
        tech = Technicians.objects.create(user=user, specialization='IT')
        other_user = Authentication.objects.create_user(username='other-profile-tech', role='TECHNICIAN')
        other = Technicians.objects.create(user=other_user, specialization='IT')
        self.client.force_authenticate(user)
        response = self.client.put(f'/api/technicians/update/{tech.pk}/', {
            'first_name': 'Sam', 'last_name': '', 'email': '', 'specialization': 'Network support',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        tech.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Sam')
        self.assertEqual(user.username, 'profile-tech')
        self.assertEqual(tech.specialization, 'Network support')
        reloaded = self.client.get('/api/technicians/').data
        self.assertEqual(reloaded[0]['first_name'], 'Sam')
        self.assertEqual(self.client.put(f'/api/technicians/update/{other.pk}/', {'first_name': 'Bad'}, format='json').status_code, 403)
