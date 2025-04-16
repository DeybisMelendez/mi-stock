from django.contrib import admin
from .models import Product, Purchase, Sale, Category

admin.site.register(Category)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "stock", "average_cost", "price")
    search_fields = ("name", "category", "description")
    list_filter = ("category",)
    ordering = ("name",)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "cost", "date", "supplier")
    list_filter = ("date", "product", "supplier")
    date_hierarchy = "date"
    ordering = ("-date",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "price", "date", "customer")
    list_filter = ("date", "product", "customer")
    date_hierarchy = "date"
    ordering = ("-date",)
