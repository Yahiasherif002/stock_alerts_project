from django.contrib import admin
from .models import Alert,TriggeredAlert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'stock', 'alert_type', 'condition', 'threshold_price', 'is_active', 'created_at']
    list_filter = ['alert_type', 'condition', 'is_active', 'created_at']
    search_fields = ['user__username', 'stock__symbol']
    readonly_fields = ['created_at', 'condition_met_since']
    

@admin.register(TriggeredAlert)
class TriggeredAlertAdmin(admin.ModelAdmin):
     ist_display = ['alert', 'stock_price', 'triggered_at', 'notification_sent']
     list_filter = ['notification_sent', 'triggered_at']
     readonly_fields = ['triggered_at']