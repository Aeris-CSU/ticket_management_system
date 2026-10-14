from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from assignments.models import Assignments
from authentication.models import Authentication
from customers.models import Customers
from technicians.models import Technicians
from tickets.models import Tickets


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AssignmentApiTests(APITestCase):
    def setUp(self):
        self.admin = Authentication.objects.create_user(username='admin', password='AdminPass123!x', role='ADMIN')
        customer_user = Authentication.objects.create_user(username='customer', password='CustomerPass123!x', role='CUSTOMER')
        self.customer = Customers.objects.create(user=customer_user, address='A')
        tech_user = Authentication.objects.create_user(username='tech', password='TechnicianPass123!x', role='TECHNICIAN')
        other_tech_user = Authentication.objects.create_user(username='tech2', password='TechnicianPass123!x', role='TECHNICIAN')
        self.tech = Technicians.objects.create(user=tech_user, specialization='IT', availability_status='AVAILABLE')
        self.other_tech = Technicians.objects.create(user=other_tech_user, specialization='Network', availability_status='AVAILABLE')
        self.ticket = Tickets.objects.create(
            problem_title='Wi-Fi', problem_description='Offline', customer=self.customer, status=Tickets.Status.OPEN,
        )

    def assign(self, technician=None):
        return self.client.post('/api/assignments/', {
            'tickets': self.ticket.pk, 'technicians': (technician or self.tech).pk,
        }, format='json')

    def test_only_admin_can_assign_and_assignment_moves_ticket_to_assigned(self):
        self.client.force_authenticate(self.customer.user)
        customer_denied = self.assign()
        self.assertEqual(customer_denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.tech.user)
        denied = self.assign()
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.admin)
        response = self.assign()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_active'])
        self.assertEqual(Tickets.objects.get(pk=self.ticket.pk).status, Tickets.Status.ASSIGNED)
        self.tech.refresh_from_db()
        self.assertEqual(self.tech.availability_status, Technicians.Availability.UNAVAILABLE)

    def test_complete_ticket_lifecycle_with_jwt_from_customer_report_to_resolution(self):
        customer_login = self.client.post('/api/login/', {
            'username': 'customer', 'password': 'CustomerPass123!x',
        }, format='json')
        self.assertEqual(customer_login.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {customer_login.data['tokens']['access']}")
        created = self.client.post('/api/tickets/', {
            'problem_title': 'Cannot log in', 'problem_description': 'School account rejected',
        }, format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        ticket_id = created.data['id']

        admin_login = self.client.post('/api/login/', {
            'username': 'admin', 'password': 'AdminPass123!x',
        }, format='json')
        self.assertEqual(admin_login.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_login.data['tokens']['access']}")
        assigned = self.client.post('/api/assignments/', {
            'tickets': ticket_id, 'technicians': self.tech.pk,
        }, format='json')
        self.assertEqual(assigned.status_code, status.HTTP_201_CREATED)
        self.assertEqual(assigned.data['tickets'], ticket_id)

        technician_login = self.client.post('/api/login/', {
            'username': 'tech', 'password': 'TechnicianPass123!x',
        }, format='json')
        self.assertEqual(technician_login.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {technician_login.data['tokens']['access']}")
        ongoing = self.client.patch(f'/api/tickets/{ticket_id}/status/', {'status': 'ONGOING'}, format='json')
        self.assertEqual(ongoing.status_code, status.HTTP_200_OK)
        self.assertEqual(ongoing.data['status'], Tickets.Status.ONGOING)
        resolved = self.client.patch(f'/api/tickets/{ticket_id}/status/', {'status': 'RESOLVED'}, format='json')
        self.assertEqual(resolved.status_code, status.HTTP_200_OK)
        self.assertEqual(resolved.data['status'], Tickets.Status.RESOLVED)
        self.assertFalse(Assignments.objects.get(pk=assigned.data['id']).is_active)
        self.tech.refresh_from_db()
        self.assertEqual(self.tech.availability_status, Technicians.Availability.AVAILABLE)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {customer_login.data['tokens']['access']}")
        customer_tickets = self.client.get('/api/tickets/')
        self.assertEqual(customer_tickets.status_code, status.HTTP_200_OK)
        self.assertEqual(customer_tickets.data[0]['status'], Tickets.Status.RESOLVED)
        self.assertEqual(self.client.get(f'/api/tickets/{ticket_id}/').data['status'], Tickets.Status.RESOLVED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_login.data['tokens']['access']}")
        assignment_history = self.client.get('/api/assignments/')
        self.assertEqual(assignment_history.status_code, status.HTTP_200_OK)
        self.assertEqual(assignment_history.data[0]['tickets'], ticket_id)
        self.assertFalse(assignment_history.data[0]['is_active'])

    def test_unavailable_technician_and_duplicate_active_assignment_are_rejected(self):
        self.other_tech.availability_status = Technicians.Availability.UNAVAILABLE
        self.other_tech.save(update_fields=['availability_status'])
        self.client.force_authenticate(self.admin)
        unavailable = self.assign(self.other_tech)
        self.assertEqual(unavailable.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Assignments.objects.exists())

        first = self.assign()
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        duplicate = self.assign(self.other_tech)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Assignments.objects.filter(tickets=self.ticket, is_active=True).count(), 1)

    def test_reassignment_keeps_history_and_moves_access_to_new_technician(self):
        self.client.force_authenticate(self.admin)
        created = self.assign()
        old = Assignments.objects.get(pk=created.data['id'])
        response = self.client.put(f"/api/assignments/{old.pk}/", {'technicians': self.other_tech.pk}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data['id'], old.pk)
        old.refresh_from_db()
        self.assertFalse(old.is_active)
        new = Assignments.objects.get(pk=response.data['id'])
        self.assertTrue(new.is_active)
        self.assertEqual(new.technicians_id, self.other_tech.pk)
        self.tech.refresh_from_db()
        self.other_tech.refresh_from_db()
        self.assertEqual(self.tech.availability_status, Technicians.Availability.AVAILABLE)
        self.assertEqual(self.other_tech.availability_status, Technicians.Availability.UNAVAILABLE)
        self.assertEqual(Tickets.objects.get(pk=self.ticket.pk).status, Tickets.Status.ASSIGNED)

        self.client.force_authenticate(self.tech.user)
        self.assertEqual(self.client.get('/api/assignments/').data, [])
        self.assertEqual(self.client.get(f'/api/assignments/{old.pk}/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(f'/api/tickets/{self.ticket.pk}/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.patch(f'/api/tickets/{self.ticket.pk}/status/', {'status': 'ONGOING'}, format='json').status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.other_tech.user)
        self.assertEqual(self.client.patch(f'/api/tickets/{self.ticket.pk}/status/', {'status': 'ONGOING'}, format='json').status_code, status.HTTP_200_OK)

    def test_resolved_or_cancelled_tickets_cannot_be_assigned(self):
        self.client.force_authenticate(self.admin)
        for terminal in (Tickets.Status.RESOLVED, Tickets.Status.CANCELLED):
            self.ticket.status = terminal
            self.ticket.save(update_fields=['status'])
            response = self.assign()
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(Assignments.objects.exists())

    def test_admin_unassign_retains_history_and_reopens_assigned_ticket(self):
        self.client.force_authenticate(self.admin)
        created = self.assign()
        response = self.client.delete(f"/api/assignments/{created.data['id']}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Assignments.objects.count(), 1)
        self.assertFalse(Assignments.objects.get().is_active)
        self.assertEqual(Tickets.objects.get(pk=self.ticket.pk).status, Tickets.Status.OPEN)
        self.tech.refresh_from_db()
        self.assertEqual(self.tech.availability_status, Technicians.Availability.AVAILABLE)

    def test_busy_technician_cannot_receive_another_ticket_or_be_marked_available(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.assign().status_code, status.HTTP_201_CREATED)
        another = Tickets.objects.create(problem_title='Printer', problem_description='Offline', customer=self.customer)
        denied = self.client.post('/api/assignments/', {'tickets': another.pk, 'technicians': self.tech.pk}, format='json')
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Assignments.objects.filter(technicians=self.tech, is_active=True).count(), 1)
        profile = self.client.put(f'/api/technicians/{self.tech.pk}/', {'availability_status': 'AVAILABLE'}, format='json')
        self.assertEqual(profile.status_code, status.HTTP_400_BAD_REQUEST)
        self.tech.refresh_from_db()
        self.assertEqual(self.tech.availability_status, Technicians.Availability.UNAVAILABLE)

    def test_cancelling_releases_technician_for_a_new_ticket(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.assign().status_code, status.HTTP_201_CREATED)
        cancelled = self.client.patch(f'/api/tickets/{self.ticket.pk}/status/', {'status': 'CANCELLED'}, format='json')
        self.assertEqual(cancelled.status_code, status.HTTP_200_OK)
        self.tech.refresh_from_db()
        self.assertEqual(self.tech.availability_status, Technicians.Availability.AVAILABLE)
        another = Tickets.objects.create(problem_title='Printer', problem_description='Offline', customer=self.customer)
        assigned = self.client.post('/api/assignments/', {'tickets': another.pk, 'technicians': self.tech.pk}, format='json')
        self.assertEqual(assigned.status_code, status.HTTP_201_CREATED)

    def test_nonexistent_assignment_returns_404(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get('/api/assignments/9999/').status_code, status.HTTP_404_NOT_FOUND)
