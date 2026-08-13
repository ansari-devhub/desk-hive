from django.contrib import admin

from apps.tickets.models import Agent, Customer, Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('subject', 'description')

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'role')
    search_fields = ('user__username', 'role')
    
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):  
    list_display = ('id', 'name', 'email')
    search_fields = ('name', 'email')