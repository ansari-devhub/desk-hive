from django.core.management.base import BaseCommand
from django.db import transaction
from apps.tenants.models import Client, Domain


class Command(BaseCommand):
    help = "Create a tenant (Client) with its Domain in one step. Idempotent — safe to rerun."

    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str, help="e.g. 'acme', 'public'")
        parser.add_argument('name', type=str, help="Display name, e.g. 'Acme Corp'")
        parser.add_argument('domain', type=str, help="e.g. 'acme.localhost' or 'localhost'")

    def handle(self, *args, **options):
        schema_name = options['schema_name']
        name = options['name']
        domain_name = options['domain']

        with transaction.atomic():
            tenant, tenant_created = Client.objects.get_or_create(
                schema_name=schema_name,
                defaults={'name': name}
            )
            domain, domain_created = Domain.objects.get_or_create(
                domain=domain_name,
                defaults={'tenant': tenant, 'is_primary': True}
            )

        if tenant_created:
            self.stdout.write(self.style.SUCCESS(f"Created tenant '{schema_name}' ({name})"))
        else:
            self.stdout.write(f"Tenant '{schema_name}' already exists — skipping.")

        if domain_created:
            self.stdout.write(self.style.SUCCESS(f"Created domain '{domain_name}' -> '{schema_name}'"))
        else:
            self.stdout.write(f"Domain '{domain_name}' already exists — skipping.")