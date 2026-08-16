from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from django.contrib.auth.models import User
from apps.tickets.models import Agent


class Command(BaseCommand):
    help = "Create a test User + Agent pair inside a given tenant schema"

    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str)
        parser.add_argument('username', type=str)
        parser.add_argument('--password', type=str, default='testpass123')
        parser.add_argument('--role', type=str, default='Support')

    def handle(self, *args, **options):
        schema_name = options['schema_name']
        username = options['username']
        password = options['password']
        role = options['role']

        with schema_context(schema_name):
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(
                    f"User '{username}' already exists in schema '{schema_name}' — skipping."
                ))
                return

            user = User.objects.create_user(username=username, password=password)
            Agent.objects.create(user=user, role=role)

            self.stdout.write(self.style.SUCCESS(
                f"Created agent '{username}' in schema '{schema_name}'"
            ))