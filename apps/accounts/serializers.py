from django.db import connection
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from apps.tickets.models import Agent


class TenantScopedTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        if not Agent.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "This user has no agent profile in this tenant."
            )

        token = super().get_token(user)
        token['schema_name'] = connection.schema_name
        return token