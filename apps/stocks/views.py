from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django.utils.translation import gettext_lazy as _
import logging

from .models import Stock
from .serializers import StockSerializer, RefreshPricesResponseSerializer
from .services import StockDataService

logger = logging.getLogger(__name__)


@extend_schema(tags=['Stocks'],description=("Manage stock data including viewing, creating, updating, and refreshing stock prices."))
class StockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stock data.
    
    Provides standard CRUD operations for stocks plus custom actions
    for refreshing stock prices.
    """
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    lookup_field = 'symbol'

    def get_queryset(self):

        queryset = Stock.objects.all()
        return queryset
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
          permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
       
        if self.action == 'refresh_prices':
            return RefreshPricesResponseSerializer
        return super().get_serializer_class()

    @extend_schema(
        summary="Refresh stock prices",
        description="Updates prices for all active stocks from external data source",
        request=None,
        responses={
            200: OpenApiResponse(
                response=RefreshPricesResponseSerializer,
                description="All prices updated successfully"
            ),
            207: OpenApiResponse(
                response=RefreshPricesResponseSerializer,
                description="Partial success - some prices failed to update"
            ),
            500: OpenApiResponse(
                description="Internal server error during price refresh"
            )
        },
        methods=['POST']
    )
    @action(
        detail=False, 
        methods=['post'],
        permission_classes=[AllowAny],
        parser_classes=[JSONParser, MultiPartParser, FormParser]
    )
    def refresh_prices(self, request):
        """
        Refresh prices for all active stocks.
        
        Returns a summary of the update operation including
        counts of successful and failed updates.
        """
        try:
            service = StockDataService()
            updated_count = service.update_all_active_stocks()
            
            # Validate that the service returned expected data structure
            if not isinstance(updated_count, dict):
                logger.error("StockDataService returned invalid response format")
                return Response(
                    {
                        'status': 'error',
                        'updated': 0,
                        'failed': 0,
                        'message': 'Invalid response from stock data service'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            updated = updated_count.get('updated', 0)
            failed = updated_count.get('failed', 0)
            
            logger.info(f"Stock price refresh completed: {updated} updated, {failed} failed")
            
            if failed > 0:
                response_data = {
                    'status': 'partial_success',
                    'updated': updated,
                    'failed': failed,
                    'message': f'Updated prices for {updated} stocks, {failed} failed'
                }
                response_status = status.HTTP_207_MULTI_STATUS
            else:
                response_data = {
                    'status': 'success',
                    'updated': updated,
                    'failed': 0,
                    'message': f'Updated prices for {updated} stocks'
                }
                response_status = status.HTTP_200_OK

            # Return response directly without serializer validation for custom actions
            # The serializer_class in @action is for OpenAPI documentation only
            return Response(response_data, status=response_status)
            
        except Exception as e:
            logger.error(f"Error during stock price refresh: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'updated': 0,
                    'failed': 0,
                    'message': 'An error occurred while refreshing stock prices'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
     
        serializer.save()

    def perform_update(self, serializer):
      
        serializer.save()

    def perform_destroy(self, instance):
       
        instance.delete()