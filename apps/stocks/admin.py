from django.contrib import admin
from .models import Stock

# Register your models here.
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'current_price', 'last_updated')
    search_fields = ('symbol', 'name')
    list_filter = ('last_updated',)

    def current_price(self, obj):
        return f"${obj.price:.2f}"
    
    current_price.short_description = 'Current Price'
