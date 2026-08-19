import pytest
from django.contrib.auth.models import User
from django_tenants.test.client import TenantClient
from django_tenants.utils import schema_context
from apps.tenants.models import Client, Domain
from apps.tickets.models import Agent, Customer, Ticket


@pytest.fixture
def tenant_with_roles(transactional_db):
    tenant = Client(schema_name='test_roles', name='Test Roles')
    tenant.save()
    Domain.objects.create(domain='test_roles.localhost', tenant=tenant, is_primary=True)

    with schema_context('test_roles'):
        owner_user = User.objects.create_user(username='owner_user', password='pass123')
        Agent.objects.create(user=owner_user, role=Agent.Role.OWNER)

        agent_user = User.objects.create_user(username='agent_user', password='pass123')
        Agent.objects.create(user=agent_user, role=Agent.Role.AGENT)

        readonly_user = User.objects.create_user(username='readonly_user', password='pass123')
        Agent.objects.create(user=readonly_user, role=Agent.Role.READ_ONLY)

        customer = Customer.objects.create(
            name="Test Customer", email="c@test.com", phone_number="+254741031179"
        )
        ticket = Ticket.objects.create(
            customer=customer, subject="Existing ticket", description="for update/delete tests"
        )

    yield tenant, ticket.id

    tenant.delete(force_drop=True)


def get_token(tenant, username):
    client = TenantClient(tenant)
    response = client.post(
        '/api/token/',
        {'username': username, 'password': 'pass123'},
        content_type='application/json',
    )
    assert response.status_code == 200, response.content
    return response.json()['access']


def test_owner_can_create_ticket(tenant_with_roles):
    tenant, _ = tenant_with_roles
    token = get_token(tenant, 'owner_user')
    client = TenantClient(tenant)

    response = client.post(
        '/api/tickets/',
        {'subject': 'New ticket', 'description': 'desc', 'customer': 1},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 201


def test_agent_can_create_ticket(tenant_with_roles):
    tenant, _ = tenant_with_roles
    token = get_token(tenant, 'agent_user')
    client = TenantClient(tenant)

    response = client.post(
        '/api/tickets/',
        {'subject': 'New ticket', 'description': 'desc', 'customer': 1},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 201


def test_readonly_cannot_create_ticket(tenant_with_roles):
    tenant, _ = tenant_with_roles
    token = get_token(tenant, 'readonly_user')
    client = TenantClient(tenant)

    response = client.post(
        '/api/tickets/',
        {'subject': 'New ticket', 'description': 'desc', 'customer': 1},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 403


def test_readonly_can_list_tickets(tenant_with_roles):
    tenant, _ = tenant_with_roles
    token = get_token(tenant, 'readonly_user')
    client = TenantClient(tenant)

    response = client.get(
        '/api/tickets/',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200


def test_agent_cannot_delete_ticket(tenant_with_roles):
    tenant, ticket_id = tenant_with_roles
    token = get_token(tenant, 'agent_user')
    client = TenantClient(tenant)

    response = client.delete(
        f'/api/tickets/{ticket_id}/',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 403


def test_owner_can_delete_ticket(tenant_with_roles):
    tenant, ticket_id = tenant_with_roles
    token = get_token(tenant, 'owner_user')
    client = TenantClient(tenant)

    response = client.delete(
        f'/api/tickets/{ticket_id}/',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 204