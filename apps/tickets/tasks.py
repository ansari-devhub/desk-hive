import logging
from celery import shared_task
from django.conf import settings
from django_tenants.utils import schema_context
import africastalking
from decouple import config

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_ticket_sms(self, ticket_id, schema_name):
    with schema_context(schema_name):
        from .models import Ticket

        try:
            ticket = Ticket.objects.select_related('customer').get(id=ticket_id)
        except Ticket.DoesNotExist:
            logger.error(f"send_ticket_sms: Ticket {ticket_id} not found in schema {schema_name}")
            return  # nothing to retry,, the ticket genuinely doesn't exist, don't keep trying

        try:
            africastalking.initialize(
                username=config('AT_USERNAME'),
                api_key=config('AT_API_KEY'),
            )
            sms = africastalking.SMS

            response = sms.send(
                message=f"Hi {ticket.customer.name}, we received your ticket: '{ticket.subject}'. We'll be in touch soon.",
                recipients=[str(ticket.customer.phone_number)],
            )
            logger.info(f"SMS sent for ticket {ticket_id} (schema {schema_name}): {response}")
            return response

        except Exception as exc:
            logger.warning(
                f"SMS send failed for ticket {ticket_id} (schema {schema_name}), "
                f"attempt {self.request.retries + 1}/{self.max_retries + 1}: {exc}"
            )
            raise self.retry(exc=exc)