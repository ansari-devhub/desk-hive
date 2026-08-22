from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from datetime import timedelta
from django.utils import timezone
from apps.tickets.models import Ticket
from django_tenants.utils import schema_context
from dateutil.relativedelta import relativedelta
from phonenumber_field.modelfields import PhoneNumberField



class Client(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)

    # auto_create_schema is a django-tenants setting: when True (default),
    # saving a new Client automatically creates its Postgres schema for you.
    auto_create_schema = True


class Domain(DomainMixin):
    pass


class Plan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    max_agents = models.PositiveIntegerField()
    max_tickets_per_month = models.PositiveIntegerField()
    price_kes = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        PAST_DUE = 'PAST_DUE', 'Past Due'
        CANCELLED = 'CANCELLED', 'Cancelled'

    tenant = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    def renew(self):
        self.current_period_end = timezone.now() + relativedelta(months=1)
        self.status = self.Status.ACTIVE
        self.save()

    def current_period_start(self):
        return self.current_period_end - relativedelta(months=1) if self.current_period_end else self.started_at

    def tickets_used_this_period(self):
        with schema_context(self.tenant.schema_name):
            return Ticket.objects.filter(created_at__gte=self.current_period_start()).count()

    def is_over_ticket_limit(self):
        return self.tickets_used_this_period() >= self.plan.max_tickets_per_month

    def __str__(self):
        return f'{self.tenant.name} — {self.plan.name} ({self.status})'
    
    
class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    amount_kes = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = PhoneNumberField()

    checkout_request_id = models.CharField(max_length=100, unique=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    initiated_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def mark_success(self, mpesa_receipt_number):

        if self.status == self.Status.SUCCESS:
            # Already processed — Safaricom can call back more than once.
            # Don't renew the subscription twice for the same payment.
            return

        self.status = self.Status.SUCCESS
        self.mpesa_receipt_number = mpesa_receipt_number
        self.confirmed_at = timezone.now()
        self.save()

        self.subscription.renew()

    def mark_failed(self):
        from django.utils import timezone

        if self.status != self.Status.PENDING:
            return

        self.status = self.Status.FAILED
        self.confirmed_at = timezone.now()
        self.save()

    def __str__(self):
        return f'{self.amount_kes} KES for {self.subscription.tenant.name} — {self.status}'