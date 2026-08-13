from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Client(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)

    # auto_create_schema is a django-tenants setting: when True (default),
    # saving a new Client automatically creates its Postgres schema for you.
    auto_create_schema = True


class Domain(DomainMixin):
    pass