from rest_framework import serializers
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturaltime
from .models import Alert, TriggeredAlert

class AlertSerializer(serializers.ModelSerializer):
    created_at_humanized = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    condition_met_since_humanized = serializers.SerializerMethodField()
    condition_met_since_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            'id', 'user', 'stock', 'alert_type', 'condition', 'threshold_price',
            'duration_minutes', 'is_active', 
            'created_at', 'created_at_humanized', 'created_at_formatted',
            'condition_met_since', 'condition_met_since_humanized', 'condition_met_since_formatted',
        ]
        read_only_fields = ['id', 'created_at', 'condition_met_since']

    def get_created_at_humanized(self, obj):
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return naturaltime(local_time)
        return None
    
    def get_created_at_formatted(self, obj):
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime("%b %d, %Y, %I:%M %p")
        return None

    def get_condition_met_since_humanized(self, obj):
        if obj.condition_met_since:
            local_time = timezone.localtime(obj.condition_met_since)
            return naturaltime(local_time)
        return None
    
    def get_condition_met_since_formatted(self, obj):
        if obj.condition_met_since:
            local_time = timezone.localtime(obj.condition_met_since)
            return local_time.strftime("%b %d, %Y, %I:%M %p")
        return None


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
    triggered_at_humanized = serializers.SerializerMethodField()
    triggered_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = TriggeredAlert
        fields = [
            'id', 'alert', 'stock_price', 'notification_sent', 'triggered_at',
            'triggered_at_humanized', 'triggered_at_formatted'
        ]

    def get_triggered_at_humanized(self, obj):
        if obj.triggered_at:
            local_time = timezone.localtime(obj.triggered_at)
            return naturaltime(local_time)
        return None
    
    def get_triggered_at_formatted(self, obj):
        if obj.triggered_at:
            local_time = timezone.localtime(obj.triggered_at)
            return local_time.strftime("%b %d, %Y, %I:%M %p")
        return None
