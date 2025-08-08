from urllib import request
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Alert, TriggeredAlert
from .serializers import (
    AlertSerializer, AlertCreateSerializer, AlertUpdateSerializer,
    TriggeredAlertSerializer
)
from .services import AlertProcessor
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Alerts'])
class AlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stock alerts
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return AlertCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AlertUpdateSerializer
        return AlertSerializer
    
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        
    
    @action(detail=False, methods=['post'])
    def test_process_alerts(self, request):
        """
        Endpoint to process all active alerts and trigger notifications
        """
        processor = AlertProcessor()
        results = processor.process_all_alerts()
        
        return Response({
            'status': 'success',
            'results': results
        })
    
    @action(detail=False, methods=['get'])
    def triggered_alerts(self, request):
        """
        Endpoint to get all triggered alerts for the authenticated user
        """
        processor = AlertProcessor()
        summary = processor.get_triggered_alert_summary(request.user)
        return Response({
            'status': 'success',
            'summary': summary
        })


@extend_schema(tags=['Triggered Alerts'])
class TriggeredAlertViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Triggered Alerts - Read-only list of triggered alerts.
    """
    serializer_class = TriggeredAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TriggeredAlert.objects.filter(
            alert__user=self.request.user
        ).order_by('-triggered_at')