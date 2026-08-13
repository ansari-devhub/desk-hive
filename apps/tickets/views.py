from rest_framework import viewsets

from apps.tickets.tasks import send_ticket_sms
from .serializers import TicketSerializer
from .models import Ticket

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    
    def perform_create(self, serializer):
        ticket = serializer.save()
        send_ticket_sms.delay(ticket.id, self.request.tenant.schema_name)