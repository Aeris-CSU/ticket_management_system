from django.test import override_settings
from rest_framework.test import APITestCase
from authentication.models import Authentication
from customers.models import Customers
from technicians.models import Technicians
from tickets.models import Tickets
from assignments.models import Assignments


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class TechnicianHistoryTests(APITestCase):
    def setUp(self):
        self.user = Authentication.objects.create_user(username='history-tech', role='TECHNICIAN')
        self.tech = Technicians.objects.create(user=self.user, specialization='IT')
        self.other_user = Authentication.objects.create_user(username='history-other', role='TECHNICIAN')
        self.other = Technicians.objects.create(user=self.other_user, specialization='IT')
        owner = Authentication.objects.create_user(username='history-customer', role='CUSTOMER')
        self.customer = Customers.objects.create(user=owner)
        self.admin = Authentication.objects.create_user(username='history-admin', role='ADMIN')
        self.ticket = Tickets.objects.create(customer=self.customer, problem_title='Printer problem', problem_description='Paper jam')

    def test_only_own_inactive_assignments_are_visible_and_read_only(self):
        old = Assignments.objects.create(tickets=self.ticket, technicians=self.tech, is_active=False, end_reason='REASSIGNED')
        foreign = Assignments.objects.create(tickets=self.ticket, technicians=self.other, is_active=False)
        active = Assignments.objects.create(tickets=self.ticket, technicians=self.tech, is_active=True)
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/assignments/history/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['results']], [old.pk])
        for record in (foreign, active):
            self.assertEqual(self.client.get(f'/api/assignments/history/{record.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/assignments/history/{old.pk}/').status_code, 200)
        self.assertEqual(self.client.put(f'/api/assignments/history/{old.pk}/', {}).status_code, 405)
        self.assertEqual(self.client.get('/api/assignments/history/?search=printer&outcome=RESOLVED').data['count'], 0)
        self.assertEqual(self.client.get('/api/assignments/history/?search=printer&outcome=REASSIGNED').data['count'], 1)
        self.client.force_authenticate(self.customer.user)
        self.assertEqual(self.client.get('/api/assignments/history/').status_code, 403)

    def test_reassignment_then_resolution_does_not_change_previous_outcome(self):
        self.client.force_authenticate(self.admin)
        result = self.client.post('/api/assignments/', {'tickets': self.ticket.pk, 'technicians': self.tech.pk}, format='json')
        self.assertEqual(result.status_code, 201)
        old_id = result.data['id']
        response = self.client.put(f'/api/assignments/{old_id}/', {'technicians': self.other.pk}, format='json')
        self.assertEqual(response.status_code, 200)
        self.client.force_authenticate(self.other_user)
        for current in ('ONGOING', 'RESOLVED'):
            self.assertEqual(self.client.patch(f'/api/tickets/{self.ticket.pk}/status/', {'status': current}, format='json').status_code, 200)
        old = Assignments.objects.get(pk=old_id)
        self.assertEqual(old.end_reason, 'REASSIGNED')
        self.assertIsNotNone(old.ended_at)
        latest = Assignments.objects.get(pk=response.data['id'])
        self.assertEqual(latest.end_reason, 'RESOLVED')
        self.assertIsNotNone(latest.ended_at)
        self.client.force_authenticate(self.user)
        row = self.client.get('/api/assignments/history/').data['results'][0]
        self.assertEqual(row['end_reason'], 'REASSIGNED')
        self.assertEqual(row['current_status'], 'RESOLVED')
        self.assertEqual(self.client.patch(f'/api/tickets/{self.ticket.pk}/status/', {'status': 'ONGOING'}, format='json').status_code, 400)

    def test_legacy_records_do_not_invent_an_outcome_and_removed_tickets_are_hidden(self):
        old = Assignments.objects.create(tickets=self.ticket, technicians=self.tech, is_active=False)
        self.client.force_authenticate(self.user)
        row = self.client.get('/api/assignments/history/?outcome=PREVIOUS').data['results'][0]
        self.assertEqual(row['end_reason'], '')
        self.assertIsNone(row['ended_at'])
        from django.utils import timezone
        self.ticket.deleted_at = timezone.now()
        self.ticket.save(update_fields=['deleted_at'])
        self.assertEqual(self.client.get('/api/assignments/history/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/assignments/history/{old.pk}/').status_code, 404)
