from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.authentication.views import CustomTokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),

    # JWT login
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # App routes with namespaces
    path('api/stocks/', include(('apps.stocks.urls', 'stocks'), namespace='stocks')),
    path('api/alerts/', include(('apps.alerts.urls', 'alerts'), namespace='alerts')),
    path('api/users/', include(('apps.authentication.urls', 'users'), namespace='users')),

    # Schema generation endpoint
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger & Redoc
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
