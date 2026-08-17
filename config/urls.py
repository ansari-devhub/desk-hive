from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import TenantScopedTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TenantScopedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('ping/', lambda request: HttpResponse('pong')),
    path('api/', include('apps.tickets.urls')),
]
