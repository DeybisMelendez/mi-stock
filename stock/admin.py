from django.contrib import admin
from .models import (
    Category, ExpenseCategory, Product, ProductImage, Purchase, Sale,
    Expense, PurchaseInvoice, SaleInvoice,
    OtherIncomeCategory, OtherIncome,
    Department, Customer,
)

admin.site.register(Category)
admin.site.register(ExpenseCategory)
admin.site.register(OtherIncomeCategory)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    ordering = ("name",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "whatsapp", "department", "active", "created_at")
    search_fields = ("name", "whatsapp", "address")
    list_filter = ("department", "active")
    ordering = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    can_delete = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "stock",
                    "average_cost", "price", "active")
    search_fields = ("name", "category", "description", "brand")
    list_filter = ("category", "active")
    ordering = ("name",)
    inlines = [ProductImageInline]


class PurchaseInline(admin.TabularInline):
    model = Purchase
    extra = 1
    can_delete = True


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ("date", "supplier", "created_at")
    list_filter = ("date", "supplier")
    date_hierarchy = "date"
    ordering = ("-date",)
    inlines = [PurchaseInline]


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("invoice", "product", "quantity", "cost")
    list_filter = ("product",)
    ordering = ("-created_at",)


class SaleInline(admin.TabularInline):
    model = Sale
    extra = 1
    can_delete = True


@admin.register(SaleInvoice)
class SaleInvoiceAdmin(admin.ModelAdmin):
    list_display = ("date", "customer_obj", "created_at")
    list_filter = ("date", "customer_obj")
    date_hierarchy = "date"
    ordering = ("-date",)
    inlines = [SaleInline]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("invoice", "product", "quantity", "price", "cost")
    list_filter = ("product",)
    ordering = ("-created_at",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("date", "category", "amount", "description", "created_at")
    list_filter = ("date", "category")
    search_fields = ("description",)
    ordering = ("-date",)


@admin.register(OtherIncome)
class OtherIncomeAdmin(admin.ModelAdmin):
    list_display = ("date", "category", "amount", "description", "created_at")
    list_filter = ("date", "category")
    search_fields = ("description",)
    ordering = ("-date",)