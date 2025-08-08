from rest_framework import serializers
from .models import Alert, TriggeredAlert

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            'id', 'user', 'stock', 'alert_type', 'condition', 'threshold_price',
            'duration_minutes', 'is_active', 'created_at', 'condition_met_since'
        ]
        read_only_fields = ['id', 'created_at', 'condition_met_since']


class AlertCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            'stock', 'alert_type', 'condition', 'threshold_price',
            'duration_minutes', 'is_active'
        ]


class AlertUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            'condition', 'threshold_price', 'duration_minutes', 'is_active'
        ]
        read_only_fields = ['stock', 'alert_type', 'created_at', 'condition_met_since']


class TriggeredAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggeredAlert
        fields = [
            'id', 'alert', 'stock_price', 'notification_sent', 'triggered_at'
        ]
