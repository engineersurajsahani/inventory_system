from django.contrib import admin
from .models import Product, Transaction, Bill, BillItem

class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'price', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    list_editable = ('quantity', 'price')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'quantity', 'price', 'total_amount', 'transaction_date')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('product__name', 'notes')
    date_hierarchy = 'transaction_date'

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'total_amount', 'created_at', 'created_by')
    list_filter = ('created_at',)
    search_fields = ('customer_name', 'customer_contact')
    inlines = [BillItemInline]
    date_hierarchy = 'created_at'