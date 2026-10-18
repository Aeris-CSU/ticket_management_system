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

    def test_ticket_preserves_submitted_contact_details_when_profile_changes(self):
        self.client.force_authenticate(self.customer.user)
        response = self.client.post('/api/tickets/', {
            'problem_title': 'On-site support', 'problem_description': 'Printer offline',
            'contact_number': '+63 917 123 4567', 'address': 'Room 204',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.customer.address = 'New profile address'
        self.customer.contact_number = '09999999999'
        self.customer.save()
        detail = self.client.get(f"/api/tickets/{response.data['id']}/")
        self.assertEqual(detail.data['address'], 'Room 204')
        self.assertEqual(detail.data['customer_address'], 'Room 204')
        self.assertEqual(detail.data['contact_number'], '+63 917 123 4567')

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
                    f'/api/tickets/{ticket.pk}/status/', {'status': 'CANCELLED', 'cancellation_reason': 'Duplicate request.'}, format='json',
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

    def test_admin_cancellation_requires_reason_and_customer_can_read_it(self):
        ticket = self.create_ticket()
        self.client.force_authenticate(self.admin)
        url = f'/api/tickets/{ticket.pk}/status/'
        for reason in (None, '', '   ', 'x' * 2001):
            payload = {'status': 'CANCELLED'}
            if reason is not None:
                payload['cancellation_reason'] = reason
            self.assertEqual(self.client.patch(url, payload, format='json').status_code, 400)
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, Tickets.Status.OPEN)
        response = self.client.patch(url, {'status': 'CANCELLED', 'cancellation_reason': '  Duplicate request.  '}, format='json')
        self.assertEqual(response.status_code, 200)
        self.client.force_authenticate(self.customer.user)
        detail = self.client.get(f'/api/tickets/{ticket.pk}/')
        self.assertEqual(detail.data['cancellation_reason'], 'Duplicate request.')

    def test_customer_cannot_supply_admin_cancellation_reason(self):
        ticket = self.create_ticket()
        self.client.force_authenticate(self.customer.user)
        response = self.client.patch(f'/api/tickets/{ticket.pk}/status/', {
            'status': 'CANCELLED', 'cancellation_reason': 'Pretend admin message',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Tickets.Status.OPEN)

    def test_ticket_numbers_increment_reset_by_manila_date_and_are_not_reused(self):
        from datetime import datetime, timezone as dt_timezone
        from unittest.mock import patch
        with patch('tickets.models.timezone.now', return_value=datetime(2026, 10, 18, 15, 59, tzinfo=dt_timezone.utc)):
            first = self.create_ticket()
            second = self.create_ticket()
            self.assertEqual(first.ticket_number, 'TCK 20261018-0001')
            self.assertEqual(second.ticket_number, 'TCK 20261018-0002')
            second.delete()
            third = self.create_ticket()
            self.assertEqual(third.ticket_number, 'TCK 20261018-0003')
            first.problem_title = 'Edited'
            first.save()
            self.assertEqual(first.ticket_number, 'TCK 20261018-0001')
        with patch('tickets.models.timezone.now', return_value=datetime(2026, 10, 18, 16, 0, tzinfo=dt_timezone.utc)):
            tomorrow = self.create_ticket()
            self.assertEqual(tomorrow.ticket_number, 'TCK 20261019-0001')

    def test_api_generates_number_and_ignores_client_number(self):
        self.client.force_authenticate(self.customer.user)
        response = self.client.post('/api/tickets/', {
            'problem_title': 'Help', 'problem_description': 'Issue', 'ticket_number': 'FAKE',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertRegex(response.data['ticket_number'], r'^TCK \d{8}-\d{4,}$')
        ticket_id = response.data['id']
        self.client.force_authenticate(self.admin)
        changed = self.client.put(f'/api/tickets/{ticket_id}/', {'ticket_number': 'FAKE', 'problem_title': 'Updated'}, format='json')
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.data['ticket_number'], response.data['ticket_number'])

    def test_assigned_technician_cannot_edit_details_on_either_route(self):
        from assignments.models import Assignments
        ticket = self.create_ticket()
        ticket.status = Tickets.Status.ASSIGNED
        ticket.save(update_fields=['status'])
        Assignments.objects.create(tickets=ticket, technicians=self.technician, is_active=True)
        self.client.force_authenticate(self.technician.user)
        for prefix in ('/api/tickets/', '/api/tickets/update/'):
            response = self.client.put(f'{prefix}{ticket.pk}/', {
                'problem_title': 'Changed', 'problem_description': 'Changed',
                'customer': self.other_customer.pk, 'address': 'Changed', 'contact_number': 'Changed',
            }, format='json')
            self.assertEqual(response.status_code, 403)
        ticket.refresh_from_db()
        self.assertEqual(ticket.problem_title, 'Wi-Fi issue')
        self.assertEqual(ticket.customer_id, self.customer.pk)
        self.assertEqual(ticket.address, '')
        self.client.force_authenticate(self.admin)
        for prefix in ('/api/tickets/', '/api/tickets/update/'):
            self.assertEqual(self.client.put(f'{prefix}{ticket.pk}/', {'problem_title': 'Admin edit'}, format='json').status_code, 200)

    def test_admin_removes_terminal_tickets_and_preserves_history(self):
        from assignments.models import Assignments
        for current in (Tickets.Status.RESOLVED, Tickets.Status.CANCELLED):
            ticket = self.create_ticket()
            ticket.status = current
            ticket.save(update_fields=['status'])
            assignment = Assignments.objects.create(tickets=ticket, technicians=self.technician, is_active=False)
            self.client.force_authenticate(self.customer.user)
            self.assertEqual(self.client.delete(f'/api/tickets/{ticket.pk}/').status_code, 403)
            self.client.force_authenticate(self.admin)
            self.assertEqual(self.client.delete(f'/api/tickets/{ticket.pk}/').status_code, 204)
            ticket.refresh_from_db()
            self.assertIsNotNone(ticket.deleted_at)
            self.assertTrue(Assignments.objects.filter(pk=assignment.pk).exists())
            self.assertEqual(self.client.get(f'/api/tickets/{ticket.pk}/').status_code, 404)
            self.assertNotIn(ticket.pk, [item['id'] for item in self.client.get('/api/tickets/').data])
            self.client.force_authenticate(self.customer.user)
            self.assertNotIn(ticket.pk, [item['id'] for item in self.client.get('/api/tickets/').data])
