from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import Authentication
from customers.models import Customers
from technicians.models import Technicians
from tickets.models import Tickets


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TicketApiTests(APITestCase):
    def setUp(self):
        self.admin = Authentication.objects.create_user(username='admin', password='AdminPass123!x', role='ADMIN')
        customer_user = Authentication.objects.create_user(username='customer', password='CustomerPass123!x', role='CUSTOMER')
        other_user = Authentication.objects.create_user(username='other', password='OtherPass123!x', role='CUSTOMER')
        self.customer = Customers.objects.create(user=customer_user, address='A')
        self.other_customer = Customers.objects.create(user=other_user, address='B')
        tech_user = Authentication.objects.create_user(username='tech', password='TechnicianPass123!x', role='TECHNICIAN')
        self.technician = Technicians.objects.create(user=tech_user, specialization='IT', availability_status='AVAILABLE')

    def create_ticket(self, customer=None):
        return Tickets.objects.create(
            problem_title='Wi-Fi issue', problem_description='Cannot connect', customer=customer or self.customer,
            status=Tickets.Status.OPEN,
        )

    def test_customer_creates_ticket_and_only_sees_own_tickets(self):
        self.client.force_authenticate(self.customer.user)
        created = self.client.post('/api/tickets/', {
            'problem_title': 'Printer issue', 'problem_description': 'Printer offline',
        }, format='json')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data['status'], Tickets.Status.OPEN)
        self.assertEqual(created.data['customer'], self.customer.pk)
        self.assertNotIn('password', created.data)

        other_ticket = self.create_ticket(self.other_customer)
        listing = self.client.get('/api/tickets/')
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual([row['id'] for row in listing.data], [created.data['id']])
        self.assertEqual(self.client.get(f'/api/tickets/{other_ticket.pk}/').status_code, status.HTTP_403_FORBIDDEN)

    def test_ticket_required_fields_and_customer_cannot_impersonate_or_set_status(self):
        self.client.force_authenticate(self.customer.user)
        missing = self.client.post('/api/tickets/', {'problem_title': 'No details'}, format='json')
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        impersonate = self.client.post('/api/tickets/', {
            'problem_title': 'Other', 'problem_description': 'Not mine', 'customer': self.other_customer.pk,
        }, format='json')
        self.assertEqual(impersonate.status_code, status.HTTP_400_BAD_REQUEST)
        forged_status = self.client.post('/api/tickets/', {
            'problem_title': 'Bad state', 'problem_description': 'Test', 'status': 'RESOLVED',
        }, format='json')
        self.assertEqual(forged_status.status_code, status.HTTP_400_BAD_REQUEST)

    def test_technician_only_sees_and_changes_assigned_ticket(self):
        assigned = self.create_ticket()
        unassigned = self.create_ticket(self.other_customer)
        from assignments.models import Assignments
        assigned.status = Tickets.Status.ASSIGNED
        assigned.save(update_fields=['status'])
        Assignments.objects.create(tickets=assigned, technicians=self.technician, is_active=True)

        self.client.force_authenticate(self.technician.user)
        listed = self.client.get('/api/tickets/')
        self.assertEqual([item['id'] for item in listed.data], [assigned.pk])
        self.assertEqual(self.client.get(f'/api/tickets/{unassigned.pk}/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.patch(f'/api/tickets/{unassigned.pk}/status/', {'status': 'ONGOING'}, format='json').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/customers/').status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.other_customer.user)
        self.assertEqual(self.client.get('/api/technicians/').status_code, status.HTTP_403_FORBIDDEN)

    def test_reassigned_ticket_is_hidden_from_previous_technician(self):
        from assignments.models import Assignments

        ticket = self.create_ticket()
        ticket.status = Tickets.Status.ASSIGNED
        ticket.save(update_fields=['status'])
        previous_assignment = Assignments.objects.create(
            tickets=ticket, technicians=self.technician, is_active=False,
        )
        next_user = Authentication.objects.create_user(username='next-tech', password='TechPass123!x', role='TECHNICIAN')
        next_technician = Technicians.objects.create(
            user=next_user, specialization='Hardware', availability_status='AVAILABLE',
        )
        Assignments.objects.create(tickets=ticket, technicians=next_technician, is_active=True)

        self.client.force_authenticate(self.technician.user)
        self.assertEqual(self.client.get('/api/tickets/').data, [])
        self.assertEqual(self.client.get(f'/api/tickets/{ticket.pk}/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.client.patch(f'/api/tickets/{ticket.pk}/status/', {'status': 'ONGOING'}, format='json').status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(next_technician.user)
        self.assertEqual([row['id'] for row in self.client.get('/api/tickets/').data], [ticket.pk])
        self.assertEqual(self.client.get(f'/api/tickets/{ticket.pk}/').status_code, status.HTTP_200_OK)
        self.assertTrue(previous_assignment.pk)

    def test_transition_rules_and_terminal_ticket_restrictions(self):
        ticket = self.create_ticket()
        self.client.force_authenticate(self.admin)
        skip = self.client.patch(f'/api/tickets/{ticket.pk}/status/', {'status': 'RESOLVED'}, format='json')
        self.assertEqual(skip.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ticket.status, Tickets.Status.OPEN)
        self.assertEqual(self.client.patch(f'/api/tickets/{ticket.pk}/status/', {'status': 'ONGOING'}, format='json').status_code, status.HTTP_400_BAD_REQUEST)

        ticket.status = Tickets.Status.ASSIGNED
        ticket.save(update_fields=['status'])
        self.assertEqual(self.client.patch(f'/api/tickets/{ticket.pk}/status/', {'status': 'ONGOING'}, format='json').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.patch(f'/api/tickets/{ticket.pk}/status/', {'status': 'RESOLVED'}, format='json').status_code, status.HTTP_200_OK)
        self.assertEqual(ticket.__class__.objects.get(pk=ticket.pk).status, Tickets.Status.RESOLVED)
        edit = self.client.put(f'/api/tickets/{ticket.pk}/', {'problem_title': 'Changed'}, format='json')
        self.assertEqual(edit.status_code, status.HTTP_400_BAD_REQUEST)
        again = self.client.patch(f'/api/tickets/{ticket.pk}/status/', {'status': 'CANCELLED'}, format='json')
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_can_cancel_own_open_ticket_only(self):
        ticket = self.create_ticket()
        self.client.force_authenticate(self.customer.user)
        response = self.client.patch(f'/api/tickets/{ticket.pk}/status/', {'status': 'CANCELLED'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Tickets.objects.get(pk=ticket.pk).status, Tickets.Status.CANCELLED)

    def test_admin_can_cancel_nonterminal_tickets(self):
        self.client.force_authenticate(self.admin)
        for current in (Tickets.Status.OPEN, Tickets.Status.ASSIGNED, Tickets.Status.ONGOING):
            with self.subTest(current=current):
                ticket = self.create_ticket()
                ticket.status = current
                ticket.save(update_fields=['status'])
                response = self.client.patch(
                    f'/api/tickets/{ticket.pk}/status/', {'status': 'CANCELLED'}, format='json',
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(Tickets.objects.get(pk=ticket.pk).status, Tickets.Status.CANCELLED)

    def test_technician_can_only_start_and_resolve_assigned_tickets(self):
        from assignments.models import Assignments

        assigned = self.create_ticket()
        assigned.status = Tickets.Status.ASSIGNED
        assigned.save(update_fields=['status'])
        Assignments.objects.create(tickets=assigned, technicians=self.technician, is_active=True)
        self.client.force_authenticate(self.technician.user)

        cancelled_assigned = self.client.patch(
            f'/api/tickets/{assigned.pk}/status/', {'status': 'CANCELLED'}, format='json',
        )
        self.assertEqual(cancelled_assigned.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tickets.objects.get(pk=assigned.pk).status, Tickets.Status.ASSIGNED)

        ongoing = self.client.patch(
            f'/api/tickets/{assigned.pk}/status/', {'status': 'ONGOING'}, format='json',
        )
        self.assertEqual(ongoing.status_code, status.HTTP_200_OK)
        cancelled_ongoing = self.client.patch(
            f'/api/tickets/{assigned.pk}/status/', {'status': 'CANCELLED'}, format='json',
        )
        self.assertEqual(cancelled_ongoing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Tickets.objects.get(pk=assigned.pk).status, Tickets.Status.ONGOING)

        resolved = self.client.patch(
            f'/api/tickets/{assigned.pk}/status/', {'status': 'RESOLVED'}, format='json',
        )
        self.assertEqual(resolved.status_code, status.HTTP_200_OK)
        self.assertEqual(Tickets.objects.get(pk=assigned.pk).status, Tickets.Status.RESOLVED)

    def test_technician_cannot_create_ticket_or_access_write_endpoints_as_customer(self):
        self.client.force_authenticate(self.technician.user)
        response = self.client.post('/api/tickets/', {
            'problem_title': 'No', 'problem_description': 'No', 'customer': self.customer.pk,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
