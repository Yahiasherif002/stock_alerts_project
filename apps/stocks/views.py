from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Stock
from .serializers import StockSerializer,RefreshPricesResponseSerializer
from .services import StockDataService


# Create your views here.
@extend_schema(tags=['Stocks'])
class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'symbol'

    @extend_schema(request=None,responses=RefreshPricesResponseSerializer)
    @action(detail=False, methods=['post'])
    def refresh_prices(self, request):
        """
        Endpoint to update stock prices from external API
        """
        service = StockDataService()
        updated_count = service.update_all_active_stocks()
        if updated_count['failed'] > 0:
            return Response({
                'status': 'partial_success',
                'message': f'Updated prices for {updated_count["updated"]} stocks, {updated_count["failed"]} failed'
            }, status=207)
        
        return Response({
            'status': 'success',
            'message': f'Updated prices for {updated_count} stocks'
        })
