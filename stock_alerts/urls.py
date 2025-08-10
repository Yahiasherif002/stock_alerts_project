from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.authentication.views import CustomTokenObtainPairView, RegisterAPIView

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT Auth
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/register/', RegisterAPIView.as_view(), name='register'),

    # App URLs with namespaces and prefixes
    path('api/alerts/', include(('apps.alerts.urls', 'alerts'), namespace='alerts')),
    path('api/', include(('apps.authentication.urls', 'authentication'), namespace='authentication')),
    path('api/', include(('apps.stocks.urls', 'stocks'), namespace='stocks')),

    # OpenAPI schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
