# serializers.py
from rest_framework import serializers
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import naturaltime
from decimal import Decimal, InvalidOperation
from .models import Alert, TriggeredAlert 
from apps.stocks.models import Stock

class StockBasicSerializer(serializers.ModelSerializer):
    """Basic stock information for nested serialization"""
    class Meta:
        model = Stock
        fields = ['id', 'symbol', 'name', 'current_price', 'last_updated', 'is_active']

class AlertSerializer(serializers.ModelSerializer):
    """Enhanced Alert serializer with detailed information"""
    stock = StockBasicSerializer(read_only=True)
    created_at_humanized = serializers.SerializerMethodField()
    created_at_formatted = serializers.SerializerMethodField()
    condition_met_since_humanized = serializers.SerializerMethodField()
    condition_met_since_formatted = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    time_until_trigger = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            'id', 'user', 'stock', 'alert_type', 'condition', 'threshold_price',
            'duration_minutes', 'is_active', 'status_display',
            'created_at', 'created_at_humanized', 'created_at_formatted',
            'condition_met_since', 'condition_met_since_humanized', 
            'condition_met_since_formatted', 'time_until_trigger',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'condition_met_since']

    def get_created_at_humanized(self, obj):
        """Get human-readable creation time"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return naturaltime(local_time)
        return None
    
    def get_created_at_formatted(self, obj):
        """Get formatted creation time"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime("%b %d, %Y, %I:%M %p")
        return None

    def get_condition_met_since_humanized(self, obj):
        """Get human-readable condition met time"""
        if obj.condition_met_since:
            local_time = timezone.localtime(obj.condition_met_since)
            return naturaltime(local_time)
        return None
    
    def get_condition_met_since_formatted(self, obj):
        """Get formatted condition met time"""
        if obj.condition_met_since:
            local_time = timezone.localtime(obj.condition_met_since)
            return local_time.strftime("%b %d, %Y, %I:%M %p")
        return None

    def get_status_display(self, obj):
        """Get human-readable status"""
        if not obj.is_active:
            return "Inactive"
        elif obj.alert_type == 'THRESHOLD':
            return "Waiting for price threshold"
        elif obj.alert_type == 'DURATION':
            if obj.condition_met_since:
                return "Condition met, waiting for duration"
            else:
                return "Waiting for price condition"
        return "Active"

    def get_time_until_trigger(self, obj):
        """Calculate time until duration alert triggers"""
        if (obj.alert_type == 'DURATION' and obj.condition_met_since and 
            obj.duration_minutes and obj.is_active):
            
            from datetime import timedelta
            trigger_time = obj.condition_met_since + timedelta(minutes=obj.duration_minutes)
            now = timezone.now()
            
            if trigger_time > now:
                remaining = trigger_time - now
                total_seconds = int(remaining.total_seconds())
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                return f"{minutes}m {seconds}s remaining"
            else:
                return "Ready to trigger"
        return None


class AlertCreateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating alerts with comprehensive validation"""
    
    class Meta:
        model = Alert
        fields = [
            'stock', 'alert_type', 'condition', 'threshold_price',
            'duration_minutes', 'is_active'
        ]

    def validate_threshold_price(self, value):
        """Validate that threshold price is positive"""
        if value is None:
            raise serializers.ValidationError("Threshold price is required.")
        
        try:
            price_decimal = Decimal(str(value))
            if price_decimal <= 0:
                raise serializers.ValidationError("Threshold price must be positive (greater than 0).")
            if price_decimal > 999999.99:
                raise serializers.ValidationError("Threshold price cannot exceed $999,999.99.")
        except (InvalidOperation, TypeError, ValueError):
            raise serializers.ValidationError("Invalid price format.")
        
        return value

    def validate_duration_minutes(self, value):
        """Validate duration minutes for duration alerts"""
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError("Duration must be positive (greater than 0 minutes).")
            if value > 43200:  # 30 days in minutes
                raise serializers.ValidationError("Duration cannot exceed 30 days (43,200 minutes).")
        return value

    def validate_condition(self, value):
        """Validate condition is valid"""
        valid_conditions = ['>', '<', '>=', '<=']
        if value not in valid_conditions:
            raise serializers.ValidationError(
                f"Invalid condition. Must be one of: {', '.join(valid_conditions)}"
            )
        return value

    def validate_alert_type(self, value):
        """Validate alert type"""
        valid_types = ['THRESHOLD', 'DURATION']
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid alert type. Must be one of: {', '.join(valid_types)}"
            )
        return value

    def validate_stock(self, value):
        """Validate stock exists and is active"""
        if not value:
            raise serializers.ValidationError("Stock is required.")
        
        if not value.is_active:
            raise serializers.ValidationError("Cannot create alerts for inactive stocks.")
        
        return value

    def validate(self, data):
        """Cross-field validation"""
        alert_type = data.get('alert_type')
        duration_minutes = data.get('duration_minutes')
        stock = data.get('stock')
        threshold_price = data.get('threshold_price')
        condition = data.get('condition')

        # Duration alerts must have duration_minutes
        if alert_type == 'DURATION':
            if duration_minutes is None or duration_minutes <= 0:
                raise serializers.ValidationError({
                    'duration_minutes': 'Duration alerts must have a positive duration_minutes value.'
                })

        # Threshold alerts should not have duration_minutes
        elif alert_type == 'THRESHOLD':
            if duration_minutes is not None:
                raise serializers.ValidationError({
                    'duration_minutes': 'Threshold alerts should not have duration_minutes.'
                })

        # Check for reasonable price thresholds compared to current stock price
        if stock and threshold_price and stock.current_price:
            current_price = float(stock.current_price)
            threshold = float(threshold_price)
            
            # Warn about extremely different prices
            price_diff_ratio = abs(threshold - current_price) / current_price
            if price_diff_ratio > 10:  # More than 1000% difference
                raise serializers.ValidationError({
                    'threshold_price': f'Threshold price ${threshold} seems very different from current price ${current_price}. Please verify.'
                })

        # Check for duplicate alerts (same user, stock, type, condition, price)
        if hasattr(self, 'instance') and self.instance:
            # Update case - exclude current instance
            user = self.instance.user
        else:
            # Create case - get user from context
            user = self.context['request'].user if 'request' in self.context else None

        if user and stock:
            existing_alert = Alert.objects.filter(
                user=user,
                stock=stock,
                alert_type=alert_type,
                condition=condition,
                threshold_price=threshold_price,
                is_active=True
            )
            
            if hasattr(self, 'instance') and self.instance:
                existing_alert = existing_alert.exclude(id=self.instance.id)
            
            if existing_alert.exists():
                raise serializers.ValidationError({
                    'non_field_errors': ['You already have an identical active alert for this stock.']
                })

        return data

    def create(self, validated_data):
        """Create alert with additional validation"""
        try:
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Failed to create alert: {str(e)}")


class AlertUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alerts with validation"""
    
    class Meta:
        model = Alert
        fields = [
            'condition', 'threshold_price', 'duration_minutes', 'is_active'
        ]
        read_only_fields = ['stock', 'alert_type', 'created_at', 'condition_met_since', 'user']

    def validate_threshold_price(self, value):
        """Validate threshold price is positive"""
        if value is not None:
            try:
                price_decimal = Decimal(str(value))
                if price_decimal <= 0:
                    raise serializers.ValidationError("Threshold price must be positive.")
                if price_decimal > 999999.99:
                    raise serializers.ValidationError("Threshold price cannot exceed $999,999.99.")
            except (InvalidOperation, TypeError, ValueError):
                raise serializers.ValidationError("Invalid price format.")
        return value

    def validate_duration_minutes(self, value):
        """Validate duration minutes"""
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError("Duration must be positive.")
            if value > 43200:  # 30 days
                raise serializers.ValidationError("Duration cannot exceed 30 days.")
        return value

    def validate(self, data):
        """Cross-field validation for updates"""
        instance = getattr(self, 'instance', None)
        if not instance:
            return data

        # If changing to inactive, that's always allowed
        if 'is_active' in data and not data['is_active']:
            return data

        # Duration alerts need duration_minutes
        if instance.alert_type == 'DURATION':
            duration = data.get('duration_minutes', instance.duration_minutes)
            if duration is None or duration <= 0:
                raise serializers.ValidationError({
                    'duration_minutes': 'Duration alerts must have positive duration_minutes.'
                })

        return data


class TriggeredAlertSerializer(serializers.ModelSerializer):
    """Basic triggered alert serializer"""
    alert = AlertSerializer(read_only=True)
    triggered_at_humanized = serializers.SerializerMethodField()
    triggered_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = TriggeredAlert
        fields = [
            'id', 'alert', 'stock_price', 'notification_sent', 'triggered_at',
            'triggered_at_humanized', 'triggered_at_formatted'
        ]

    def get_triggered_at_humanized(self, obj):
        """Get human-readable trigger time"""
        if obj.triggered_at:
            local_time = timezone.localtime(obj.triggered_at)
            return naturaltime(local_time)
        return None
    
    def get_triggered_at_formatted(self, obj):
        """Get formatted trigger time"""
        if obj.triggered_at:
            local_time = timezone.localtime(obj.triggered_at)
            return local_time.strftime("%b %d, %Y, %I:%M %p")
        return None


class TriggeredAlertDetailSerializer(serializers.ModelSerializer):
    """Detailed triggered alert serializer with full alert and stock information"""
    alert_id = serializers.IntegerField(source='alert.id', read_only=True)
    alert_type = serializers.CharField(source='alert.alert_type', read_only=True)
    condition = serializers.CharField(source='alert.condition', read_only=True)
    threshold_price = serializers.DecimalField(source='alert.threshold_price', max_digits=10, decimal_places=2, read_only=True)
    duration_minutes = serializers.IntegerField(source='alert.duration_minutes', read_only=True)
    
    # Stock information
    stock_id = serializers.IntegerField(source='alert.stock.id', read_only=True)
    stock_symbol = serializers.CharField(source='alert.stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='alert.stock.name', read_only=True)
    stock_current_price = serializers.DecimalField(source='alert.stock.current_price', max_digits=10, decimal_places=2, read_only=True)
    
    # User information (for admin views)
    user_id = serializers.IntegerField(source='alert.user.id', read_only=True)
    username = serializers.CharField(source='alert.user.username', read_only=True)
    
    # Time formatting
    triggered_at_humanized = serializers.SerializerMethodField()
    triggered_at_formatted = serializers.SerializerMethodField()
    alert_created_at = serializers.DateTimeField(source='alert.created_at', read_only=True)
    
    # Additional computed fields
    price_difference = serializers.SerializerMethodField()
    price_difference_percentage = serializers.SerializerMethodField()

    class Meta:
        model = TriggeredAlert
        fields = [
            'id', 'stock_price', 'notification_sent', 'triggered_at',
            'triggered_at_humanized', 'triggered_at_formatted',
            # Alert details
            'alert_id', 'alert_type', 'condition', 'threshold_price', 
            'duration_minutes', 'alert_created_at',
            # Stock details
            'stock_id', 'stock_symbol', 'stock_name', 'stock_current_price',
            # User details (for admin)
            'user_id', 'username',
            # Computed fields
            'price_difference', 'price_difference_percentage',
        ]

    def get_triggered_at_humanized(self, obj):
        """Get human-readable trigger time"""
        if obj.triggered_at:
            local_time = timezone.localtime(obj.triggered_at)
            return naturaltime(local_time)
        return None
    
    def get_triggered_at_formatted(self, obj):
        """Get formatted trigger time"""
        if obj.triggered_at:
            local_time = timezone.localtime(obj.triggered_at)
            return local_time.strftime("%b %d, %Y, %I:%M %p")
        return None

    def get_price_difference(self, obj):
        """Calculate price difference from threshold"""
        try:
            triggered_price = float(obj.stock_price)
            threshold_price = float(obj.alert.threshold_price)
            return round(triggered_price - threshold_price, 2)
        except (TypeError, ValueError):
            return None

    def get_price_difference_percentage(self, obj):
        """Calculate percentage difference from threshold"""
        try:
            triggered_price = float(obj.stock_price)
            threshold_price = float(obj.alert.threshold_price)
            if threshold_price != 0:
                percentage = ((triggered_price - threshold_price) / threshold_price) * 100
                return round(percentage, 2)
            return 0
        except (TypeError, ValueError, ZeroDivisionError):
            return None

    def to_representation(self, instance):
        """Customize representation based on user permissions"""
        data = super().to_representation(instance)
        
        # Hide user information for non-admin users
        request = self.context.get('request')
        if request and not request.user.is_staff:
            data.pop('user_id', None)
            data.pop('username', None)
        
        return data


class AlertSummarySerializer(serializers.Serializer):
    """Serializer for alert summary statistics"""
    total_alerts = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    inactive_alerts = serializers.IntegerField()
    threshold_alerts = serializers.IntegerField()
    duration_alerts = serializers.IntegerField()
    triggered_today = serializers.IntegerField()
    triggered_this_week = serializers.IntegerField()
    triggered_total = serializers.IntegerField()
    most_triggered_stock = serializers.CharField(allow_null=True)
    avg_threshold_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)


class StockTriggerStatsSerializer(serializers.Serializer):
    """Serializer for stock-wise trigger statistics"""
    stock_symbol = serializers.CharField(source='alert__stock__symbol')
    stock_name = serializers.CharField(source='alert__stock__name')
    total_triggers = serializers.IntegerField()
    avg_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_triggered = serializers.DateTimeField()