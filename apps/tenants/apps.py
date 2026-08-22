from django.apps import AppConfig


class TenantsConfig(AppConfig):
    name = 'apps.tenants'
    
    def ready(self):
        import apps.tenants.signals