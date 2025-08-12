# views.py
from urllib import request
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Q
from .models import Alert, TriggeredAlert
from .serializers import (
    AlertSerializer, AlertCreateSerializer, AlertUpdateSerializer,
    TriggeredAlertSerializer, TriggeredAlertDetailSerializer
)
from .services import AlertProcessor
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

@extend_schema(tags=['Alerts'], description=("Manage stock alerts including creating, updating, and processing alerts."))
class AlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stock alerts with comprehensive validation and filtering
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['alert_type', 'condition', 'is_active', 'stock']
    ordering_fields = ['created_at', 'threshold_price']
    ordering = ['-created_at']
    search_fields = ['stock__symbol', 'stock__name']
    
    def get_queryset(self):
        """Return alerts for the current user with optional filtering"""
        queryset = Alert.objects.filter(user=self.request.user).select_related('stock')
        
        # Additional custom filters
        stock_symbol = self.request.query_params.get('stock_symbol', None)
        if stock_symbol:
            queryset = queryset.filter(stock__symbol__icontains=stock_symbol)
            
        price_range = self.request.query_params.get('price_range', None)
        if price_range:
            try:
                min_price, max_price = map(float, price_range.split(','))
                queryset = queryset.filter(
                    threshold_price__gte=min_price,
                    threshold_price__lte=max_price
                )
            except (ValueError, TypeError):
                pass  # Ignore invalid price range format
        
        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return AlertCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AlertUpdateSerializer
        return AlertSerializer
    
    def perform_create(self, serializer):
        """Create alert with user assignment and validation"""
        try:
            serializer.save(user=self.request.user)
        except Exception as e:
            return Response(
                {'error': f'Failed to create alert: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request, *args, **kwargs):
        """Enhanced create with better error handling"""
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
            return Response({
                'status': 'success',
                'message': 'Alert created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Failed to create alert',
                'errors': serializer.errors if hasattr(serializer, 'errors') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """Enhanced update with better error handling"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            return Response({
                'status': 'success',
                'message': 'Alert updated successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Failed to update alert',
                'errors': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Enhanced delete with confirmation"""
        try:
            instance = self.get_object()
            alert_info = f"{instance.stock.symbol} {instance.condition} ${instance.threshold_price}"
            self.perform_destroy(instance)
            
            return Response({
                'status': 'success',
                'message': f'Alert deleted successfully: {alert_info}'
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to delete alert: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Manually process all active alerts for testing",
        responses={200: {"description": "Processing results"}}
    )
    @action(detail=False, methods=['post'])
    def test_process_alerts(self, request):
        """
        Endpoint to process all active alerts and trigger notifications
        """
        try:
            processor = AlertProcessor()
            results = processor.process_all_alerts()
            
            return Response({
                'status': 'success',
                'message': 'Alert processing completed',
                'results': results
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Alert processing failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        description="Get summary of user's alerts",
        responses={200: {"description": "Alert summary"}}
    )
    @action(detail=False, methods=['get'], url_path='summary')
    def get_summary(self, request):
        """
        Endpoint to get summary of user's alerts
        """
        try:
            processor = AlertProcessor()
            summary = processor.get_user_alerts_summary(request.user)
            return Response({
                'status': 'success',
                'summary': summary
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to get summary: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        description="Get triggered alerts with full details",
        parameters=[
            OpenApiParameter(name='stock', type=OpenApiTypes.INT, description='Filter by stock ID'),
            OpenApiParameter(name='date', type=OpenApiTypes.DATE, description='Filter by date (YYYY-MM-DD)'),
            OpenApiParameter(name='limit', type=OpenApiTypes.INT, description='Limit number of results'),
        ]
    )
    @action(detail=False, methods=['get'], url_path='triggered')
    def triggered_alerts(self, request):
        """
        Enhanced endpoint to get all triggered alerts with full details
        """
        try:
            # Get base queryset
            queryset = TriggeredAlert.objects.filter(
                alert__user=request.user
            ).select_related('alert', 'alert__stock').order_by('-triggered_at')
            
            # Apply filters
            stock_id = request.query_params.get('stock')
            if stock_id:
                try:
                    stock_id = int(stock_id)
                    queryset = queryset.filter(alert__stock_id=stock_id)
                except (ValueError, TypeError):
                    return Response({
                        'status': 'error',
                        'message': 'Invalid stock ID format'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            date_filter = request.query_params.get('date')
            if date_filter:
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    queryset = queryset.filter(triggered_at__date=date_obj)
                except ValueError:
                    return Response({
                        'status': 'error',
                        'message': 'Invalid date format. Use YYYY-MM-DD'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Apply limit
            limit = request.query_params.get('limit')
            if limit:
                try:
                    limit = int(limit)
                    if limit > 0:
                        queryset = queryset[:limit]
                except (ValueError, TypeError):
                    pass
            
            # Serialize data
            serializer = TriggeredAlertDetailSerializer(queryset, many=True)
            
            # Get counts for summary
            total_count = TriggeredAlert.objects.filter(alert__user=request.user).count()
            filtered_count = queryset.count() if hasattr(queryset, 'count') else len(queryset)
            
            return Response({
                'status': 'success',
                'count': filtered_count,
                'total_triggered_alerts': total_count,
                'results': serializer.data
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to get triggered alerts: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Triggered Alerts'])
class TriggeredAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing triggered alerts with enhanced filtering
    """
    serializer_class = TriggeredAlertDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['notification_sent', 'alert__stock', 'alert__alert_type']
    ordering_fields = ['triggered_at', 'stock_price']
    ordering = ['-triggered_at']

    def get_queryset(self):
        """Return triggered alerts based on user permissions"""
        if self.request.user.is_staff:
            return TriggeredAlert.objects.all().select_related(
                'alert', 'alert__stock', 'alert__user'
            ).order_by('-triggered_at')
        else:
            return TriggeredAlert.objects.filter(
                alert__user=self.request.user
            ).select_related('alert', 'alert__stock').order_by('-triggered_at')

    def list(self, request, *args, **kwargs):
        """Enhanced list with better error handling"""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response({
                    'status': 'success',
                    'results': serializer.data
                })

            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'status': 'success',
                'count': len(serializer.data),
                'results': serializer.data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to retrieve triggered alerts: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        description="Get comprehensive summary of triggered alerts",
        responses={200: {"description": "Triggered alerts summary"}}
    )
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Enhanced endpoint to get comprehensive summary of triggered alerts
        """
        try:
            processor = AlertProcessor()
            
            if request.user.is_staff:
                summary = processor.get_all_triggered_alerts_summary()
            else:
                summary = processor.get_user_alerts_summary(request.user)

            # Additional statistics
            from django.utils import timezone
            from datetime import timedelta
            
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            
            if request.user.is_staff:
                triggered_today = TriggeredAlert.objects.filter(
                    triggered_at__date=today
                ).count()
                triggered_this_week = TriggeredAlert.objects.filter(
                    triggered_at__date__gte=week_ago
                ).count()
            else:
                triggered_today = TriggeredAlert.objects.filter(
                    alert__user=request.user,
                    triggered_at__date=today
                ).count()
                triggered_this_week = TriggeredAlert.objects.filter(
                    alert__user=request.user,
                    triggered_at__date__gte=week_ago
                ).count()

            enhanced_summary = {
                **summary,
                'triggered_today': triggered_today,
                'triggered_this_week': triggered_this_week,
                'summary_date': today.isoformat(),
            }

            return Response({
                'status': 'success',
                'summary': enhanced_summary
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to get summary: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        description="Get triggered alerts statistics by stock",
        responses={200: {"description": "Stock-wise statistics"}}
    )
    @action(detail=False, methods=['get'], url_path='stats-by-stock')
    def stats_by_stock(self, request):
        """
        Get triggered alerts statistics grouped by stock
        """
        try:
            from django.db.models import Count, Avg, Max, Min
            
            if request.user.is_staff:
                queryset = TriggeredAlert.objects.all()
            else:
                queryset = TriggeredAlert.objects.filter(alert__user=request.user)
            
            stats = queryset.values(
                'alert__stock__symbol',
                'alert__stock__name'
            ).annotate(
                total_triggers=Count('id'),
                avg_price=Avg('stock_price'),
                max_price=Max('stock_price'),
                min_price=Min('stock_price'),
                last_triggered=Max('triggered_at')
            ).order_by('-total_triggers')
            
            return Response({
                'status': 'success',
                'stats': list(stats)
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Failed to get stock statistics: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)