from .models import Authentication, Notification


def notify_ticket(ticket, event, technician=None, previous=None):
    number = ticket.ticket_number or f'#{ticket.pk}'
    admins = list(Authentication.objects.filter(role='ADMIN').values_list('pk', flat=True))
    customer = ticket.customer.user_id
    rows = []
    def add(users, text):
        for user_id in set(users):
            rows.append(Notification(recipient_id=user_id, ticket=ticket, event=event, message=text))
    if event == 'SUBMITTED':
        add(admins, f'New ticket {number} was submitted by a customer.')
        add([customer], f'Your ticket {number} was submitted successfully.')
    elif event == 'ASSIGNED':
        add(admins, f'Ticket {number} was assigned to a technician.')
        add([customer], f'A technician has been assigned to your ticket {number}.')
        add([technician.user_id], f'You have been assigned ticket {number}.')
        if previous:
            add([previous.user_id], f'Ticket {number} has been reassigned to another technician.')
    elif event in ('ONGOING', 'RESOLVED', 'CANCELLED'):
        verb = {'ONGOING': 'is now ongoing', 'RESOLVED': 'has been resolved', 'CANCELLED': 'was cancelled'}[event]
        add(admins, f'Ticket {number} {verb}.')
        customer_verb = {'ONGOING': 'is now being worked on', 'RESOLVED': 'has been resolved', 'CANCELLED': 'has been cancelled'}[event]
        message = f'Your ticket {number} {customer_verb}.'
        if event == 'CANCELLED' and ticket.cancellation_reason:
            message += f' Reason: {ticket.cancellation_reason}'
        add([customer], message[:500])
        if event == 'CANCELLED':
            add(ticket.assignments_set.filter(is_active=True).values_list('technicians__user_id', flat=True), f'Your assigned ticket {number} has been cancelled.')
    Notification.objects.bulk_create(rows)
