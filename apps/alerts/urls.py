# apps/alerts/urls.py
from rest_framework.routers import DefaultRouter
from .views import AlertViewSet, TriggeredAlertViewSet

app_name = "alerts"

router = DefaultRouter()
router.register("alerts", AlertViewSet, basename="alert")
router.register("triggered", TriggeredAlertViewSet, basename="triggeredalert")

urlpatterns = router.urls
