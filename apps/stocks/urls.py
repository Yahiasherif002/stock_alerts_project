from rest_framework.routers import DefaultRouter
from .views import StockViewSet

app_name = 'stocks'

router = DefaultRouter()
router.register(r'stocks', StockViewSet, basename='stock')

urlpatterns = router.urls
