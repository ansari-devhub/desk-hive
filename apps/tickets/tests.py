import pytest
from django_tenants.utils import schema_context
from apps.tenants.models import Client
from .models import Customer, Ticket


@pytest.fixture
def tenants(transactional_db):
    tenant_a = Client(schema_name="test_acme", name="Test Acme")
    tenant_a.save()

    tenant_b = Client(schema_name="test_globex", name="Test Globex")
    tenant_b.save()

    yield tenant_a, tenant_b

    tenant_a.delete(force_drop=True)
    tenant_b.delete(force_drop=True)


@pytest.mark.django_db
def test_tickets_do_not_leak_across_tenants(tenants):
    with schema_context("test_acme"):
        customer = Customer.objects.create(
            name="Acme User",
            email="a@acme.com"
        )
        Ticket.objects.create(
            customer=customer,
            subject="Acme-only ticket",
            description="..."
        )

        assert Ticket.objects.count() == 1

    with schema_context("test_globex"):
        assert Ticket.objects.count() == 0

    with schema_context("test_acme"):
        assert Ticket.objects.count() == 1