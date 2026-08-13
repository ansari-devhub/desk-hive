from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from apps.tickets.models import Customer, Ticket
from apps.tickets.tasks import send_ticket_sms


class Command(BaseCommand):
    help = "Create a test ticket in the acme tenant and trigger the SMS task"

    def handle(self, *args, **options):
        with schema_context('acme'):
            customer = Customer.objects.create(
                name="Test User", email="t@test.com", phone_number="+254741031179"
            )
            ticket = Ticket.objects.create(
                customer=customer, subject="SMS test", description="testing celery + sms"
            )
            send_ticket_sms.delay(ticket.id, 'acme')
            self.stdout.write(self.style.SUCCESS(f"Ticket {ticket.id} created, SMS task queued"))