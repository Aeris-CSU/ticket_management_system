from zoneinfo import ZoneInfo
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
from customers.models import Customers

class TicketDailyCounter(models.Model):
    date = models.DateField(unique=True)
    last_number = models.PositiveIntegerField(default=0)


class Tickets(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        ONGOING = 'ONGOING', 'Ongoing'
        RESOLVED = 'RESOLVED', 'Resolved'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.AutoField(primary_key=True)
    ticket_number = models.CharField(max_length=40, unique=True, editable=False)
    problem_title = models.CharField(max_length=200)
    problem_description = models.TextField()
    contact_number = models.CharField(max_length=30, blank=True, default='')
    address = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)
    cancellation_reason = models.TextField(blank=True, default='', max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(Customers, on_delete=models.PROTECT)


    def save(self, *args, **kwargs):
        if self._state.adding and not self.ticket_number:
            using = kwargs.get('using') or 'default'
            with transaction.atomic(using=using):
                day = timezone.localtime(timezone.now(), ZoneInfo('Asia/Manila')).date()
                counter, _ = TicketDailyCounter.objects.using(using).get_or_create(date=day)
                TicketDailyCounter.objects.using(using).filter(pk=counter.pk).update(last_number=F('last_number') + 1)
                counter.refresh_from_db(using=using)
                self.ticket_number = f'TCK {day:%Y%m%d}-{counter.last_number:04d}'
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)
