from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Client, Plan, Subscription


@receiver(post_save, sender=Client)
def create_default_subscription(sender, instance, created, **kwargs):
    if created and instance.schema_name != 'public':
        free_plan, _ = Plan.objects.get_or_create(
            name='Free',
            defaults={'max_agents': 2, 'max_tickets_per_month': 50, 'price_kes': 0}
        )
        Subscription.objects.get_or_create(tenant=instance, defaults={'plan': free_plan})