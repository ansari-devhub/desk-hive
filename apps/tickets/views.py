import logging
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from apps.tickets.models import Ticket
from apps.tickets.permissions import TicketPermission
from apps.tickets.serializers import TicketSerializer
from apps.tickets.tasks import send_ticket_sms

logger = logging.getLogger(__name__)


class TicketViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, TicketPermission]
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def create(self, request, *args, **kwargs):
        subscription = request.tenant.subscription
        if subscription.is_over_ticket_limit():
            raise PermissionDenied(
                f"Monthly ticket limit ({subscription.plan.max_tickets_per_month}) reached for the {subscription.plan.name} plan."
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()

        sms_queued = True
        try:
            send_ticket_sms.delay(ticket.id, self.request.tenant.schema_name)
        except Exception as exc:
            sms_queued = False
            logger.error(f"Failed to queue SMS task for ticket {ticket.id}: {exc}")

        response_data = serializer.data
        if not sms_queued:
            response_data['warning'] = "Ticket created, but SMS notification could not be queued."

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)