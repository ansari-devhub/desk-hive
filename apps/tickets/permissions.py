from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Agent


class TicketPermission(BasePermission):
    """
    Owner: full access.
    Agent: read + create + update, no delete.
    Read-only: read only.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            agent = Agent.objects.get(user=request.user)
        except Agent.DoesNotExist:
            return False

        request.agent = agent  # cache it, avoid a second query in has_object_permission

        if agent.role == Agent.Role.OWNER:
            return True

        if agent.role == Agent.Role.AGENT:
            return request.method != 'DELETE'

        if agent.role == Agent.Role.READ_ONLY:
            return request.method in SAFE_METHODS

        return False