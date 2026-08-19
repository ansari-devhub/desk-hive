from rest_framework import serializers
from .models import Ticket, Agent, Customer


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'subject', 'description', 'status', 'customer', 'agent', 'custom_fields', 'created_at', 'updated_at']