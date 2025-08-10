from rest_framework import serializers
from .models import Stock

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = [
            'id', 'symbol', 'name', 'current_price', 'last_updated',
            'is_active', 'created_at'
        ]
        

class RefreshPricesResponseSerializer(serializers.Serializer):
    """
    Serializer for the refresh_prices action response.
    """
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial_success', 'Partial Success'),
        ('error', 'Error'),
    ]
    
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    updated = serializers.IntegerField(min_value=0)
    failed = serializers.IntegerField(min_value=0)
    message = serializers.CharField(max_length=255)

    def validate(self, data):
        """
        Validate that the data is consistent.
        """
        if data['status'] == 'success' and data['failed'] > 0:
            raise serializers.ValidationError(
                "Status cannot be 'success' if there are failed updates"
            )
        
        if data['status'] == 'partial_success' and data['failed'] == 0:
            raise serializers.ValidationError(
                "Status cannot be 'partial_success' if there are no failed updates"
            )
            
        return data