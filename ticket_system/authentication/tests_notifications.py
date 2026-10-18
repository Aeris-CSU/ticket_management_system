from django.test import override_settings
from rest_framework.test import APITestCase
from authentication.models import Authentication, Notification
from customers.models import Customers
from technicians.models import Technicians


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class NotificationTests(APITestCase):
    def setUp(self):
        Authentication.objects.filter(role='ADMIN').delete()
        self.admin = Authentication.objects.create_user(username='notify-admin', role='ADMIN')
        self.owner = Authentication.objects.create_user(username='notify-owner', role='CUSTOMER')
        self.other = Authentication.objects.create_user(username='notify-other', role='CUSTOMER')
        self.customer = Customers.objects.create(user=self.owner, address='Home')
        self.tech_user = Authentication.objects.create_user(username='notify-tech', role='TECHNICIAN')
        self.tech = Technicians.objects.create(user=self.tech_user, specialization='IT')
        self.tech2_user = Authentication.objects.create_user(username='notify-tech2', role='TECHNICIAN')
        self.tech2 = Technicians.objects.create(user=self.tech2_user, specialization='IT')

    def submit(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post('/api/tickets/', {'problem_title': 'Network issue', 'problem_description': 'Offline'}, format='json')
        self.assertEqual(response.status_code, 201)
        return response.data['id']

    def assign(self, ticket):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/assignments/', {'tickets': ticket, 'technicians': self.tech.pk}, format='json')
        self.assertEqual(response.status_code, 201)
        return response.data['id']

    def test_submission_assignment_work_and_resolution_recipients(self):
        ticket = self.submit()
        self.assertEqual(set(Notification.objects.filter(event='SUBMITTED').values_list('recipient_id', flat=True)), {self.admin.pk, self.owner.pk})
        self.assign(ticket)
        self.assertEqual(set(Notification.objects.filter(event='ASSIGNED').values_list('recipient_id', flat=True)), {self.admin.pk, self.owner.pk, self.tech_user.pk})
        self.client.force_authenticate(self.tech_user)
        for current in ('ONGOING', 'RESOLVED'):
            self.assertEqual(self.client.patch(f'/api/tickets/{ticket}/status/', {'status': current}, format='json').status_code, 200)
            self.assertEqual(set(Notification.objects.filter(event=current).values_list('recipient_id', flat=True)), {self.admin.pk, self.owner.pk})
        self.assertFalse(Notification.objects.filter(recipient=self.other).exists())
        self.assertTrue(all(row['ticket_id'] is None for row in self.client.get('/api/notifications/').data['results']))
        count = Notification.objects.count()
        self.assertEqual(self.client.patch(f'/api/tickets/{ticket}/status/', {'status': 'RESOLVED'}, format='json').status_code, 400)
        self.assertEqual(Notification.objects.count(), count)

    def test_reassignment_and_cancellation_only_notify_relevant_technicians(self):
        ticket = self.submit()
        assignment = self.assign(ticket)
        response = self.client.put(f'/api/assignments/{assignment}/', {'technicians': self.tech2.pk}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Notification.objects.filter(recipient=self.tech_user, message__contains='reassigned to another').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.tech2_user, message__contains='You have been assigned').exists())
        self.client.force_authenticate(self.tech_user)
        self.assertTrue(all(row['ticket_id'] is None for row in self.client.get('/api/notifications/').data['results']))
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.patch(f'/api/tickets/{ticket}/status/', {'status': 'CANCELLED', 'cancellation_reason': 'Duplicate report.'}, format='json').status_code, 200)
        self.assertEqual(set(Notification.objects.filter(event='CANCELLED').values_list('recipient_id', flat=True)), {self.admin.pk, self.owner.pk, self.tech2_user.pk})

    def test_read_delete_filters_and_recipient_isolation(self):
        self.submit()
        own = Notification.objects.get(recipient=self.owner)
        foreign = Notification.objects.get(recipient=self.admin)
        response = self.client.get('/api/notifications/?filter=unread')
        self.assertEqual(response.data['unread_count'], 1)
        self.assertEqual([row['id'] for row in response.data['results']], [own.pk])
        self.assertEqual(self.client.post('/api/notifications/', {'action': 'read', 'ids': [own.pk, foreign.pk]}, format='json').status_code, 200)
        foreign.refresh_from_db()
        self.assertFalse(foreign.is_read)
        self.assertEqual(self.client.get('/api/notifications/?filter=unread').data['total'], 0)
        self.assertEqual(self.client.get('/api/notifications/').data['total'], 1)
        self.assertEqual(self.client.post('/api/notifications/', {'action': 'delete'}, format='json').status_code, 400)
        self.client.post('/api/notifications/', {'action': 'delete', 'all': True}, format='json')
        self.assertFalse(Notification.objects.filter(recipient=self.owner).exists())
        self.assertTrue(Notification.objects.filter(pk=foreign.pk).exists())
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/notifications/').status_code, 401)

    def test_pagination_and_deleted_ticket_links(self):
        ticket = self.submit()
        own = Notification.objects.get(recipient=self.owner)
        from tickets.models import Tickets
        Tickets.objects.filter(pk=ticket).update(deleted_at=own.created_at)
        self.assertIsNone(self.client.get('/api/notifications/').data['results'][0]['ticket_id'])
        Notification.objects.bulk_create([Notification(recipient=self.owner, event='TEST', message='History') for _ in range(32)])
        self.assertEqual(len(self.client.get('/api/notifications/').data['results']), 30)
        self.assertEqual(len(self.client.get('/api/notifications/?page=2').data['results']), 3)
