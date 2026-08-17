from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings

# Create your models here.
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
    
class Agent(models.Model):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        AGENT = 'AGENT', 'Agent'
        READ_ONLY = 'READ_ONLY', 'Read-only'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agent_profile')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.AGENT)

    def __str__(self):
        return f'{self.user.username}: {self.role}'
    
class Customer(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = PhoneNumberField()
    
    def __str__(self):
        return f'{self.name}'
    
class Ticket(TimeStampedModel):
    class TicketStatus(models.TextChoices):
        OPEN = 'OPEN', 'open',
        PENDING = 'PENDING', 'pending',
        RESOLVED = 'RESOLVED', 'resolved',
        CLOSED = 'CLOSED', 'closed'
        
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_tickets')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, related_name='agent_tickets', null=True, blank=True)
    subject = models.CharField(max_length=200)    
    description = models.TextField()
    status = models.CharField(
        max_length=9,
        choices=TicketStatus,
        default=TicketStatus.OPEN
    )
    
    def __str__(self):
        return f'{self.subject}'