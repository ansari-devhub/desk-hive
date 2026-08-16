# apps/accounts/authentication.py  (new small app, or put in apps/tickets/ for now)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from apps.tickets.models import Agent


class TenantAwareJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None

        user, validated_token = result

        if not Agent.objects.filter(user=user).exists():
            raise AuthenticationFailed(
                "User has no agent profile in this tenant."
            )

        return user, validated_token