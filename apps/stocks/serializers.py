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
    status = serializers.CharField()
    message = serializers.CharField()        