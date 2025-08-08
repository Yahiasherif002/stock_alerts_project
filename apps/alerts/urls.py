from rest_framework.routers import DefaultRouter
from .views import AlertViewSet, TriggeredAlertViewSet

router = DefaultRouter()
router.register(r'', AlertViewSet, basename='alert')
router.register(r'triggered', TriggeredAlertViewSet, basename='triggeredalert')

urlpatterns = router.urls
