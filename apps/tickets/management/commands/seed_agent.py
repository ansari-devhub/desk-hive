from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from django.contrib.auth.models import User
from apps.tickets.models import Agent


class Command(BaseCommand):
    help = "Create or update a User + Agent pair inside a given tenant schema"

    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str)
        parser.add_argument('username', type=str)
        parser.add_argument('--password', type=str, default='testpass123')
        parser.add_argument('--role', type=str, default=Agent.Role.AGENT, choices=Agent.Role.values)

    def handle(self, *args, **options):
        schema_name = options['schema_name']
        username = options['username']
        password = options['password']
        role = options['role']

        with schema_context(schema_name):
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.save()

            agent, agent_created = Agent.objects.get_or_create(user=user, defaults={'role': role})

            if not agent_created and agent.role != role:
                old_role = agent.role
                agent.role = role
                agent.save()
                self.stdout.write(self.style.WARNING(
                    f"Updated '{username}' role: '{old_role}' → '{role}'"
                ))
            elif agent_created:
                self.stdout.write(self.style.SUCCESS(
                    f"Created agent '{username}' with role '{role}' in schema '{schema_name}'"
                ))
            else:
                self.stdout.write(f"'{username}' already has role '{role}' — no change.")