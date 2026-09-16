from django.contrib import admin
from .models import (
    Category, ExpenseCategory, Product, ProductImage, Purchase, Sale,
    Expense, PurchaseInvoice, SaleInvoice,
    OtherIncomeCategory, OtherIncome,
    Department, Customer,
    Tag, VoidedInvoiceLine,
)

admin.site.register(Category)
admin.site.register(ExpenseCategory)
admin.site.register(OtherIncomeCategory)
admin.site.register(Tag)


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
    list_display = ("name", "category", "stock",
                    "average_cost", "price", "active")
    search_fields = ("name", "category", "description")
    list_filter = ("category", "active", "tags")
    filter_horizontal = ("tags",)
    ordering = ("name",)
    inlines = [ProductImageInline]


class PurchaseInline(admin.TabularInline):
    model = Purchase
    extra = 1
    can_delete = True


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ("date", "supplier", "voided", "voided_at", "created_at")
    list_filter = ("date", "supplier", "voided")
    date_hierarchy = "date"
    ordering = ("-date",)
    inlines = [PurchaseInline]
    readonly_fields = ("voided_at", "voided_by", "created_at")


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
    list_display = ("date", "customer_obj", "voided", "voided_at", "created_at")
    list_filter = ("date", "customer_obj", "voided")
    date_hierarchy = "date"
    ordering = ("-date",)
    inlines = [SaleInline]
    readonly_fields = ("voided_at", "voided_by", "created_at")


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


@admin.register(VoidedInvoiceLine)
class VoidedInvoiceLineAdmin(admin.ModelAdmin):
    list_display = ("invoice_kind", "invoice_id", "product", "quantity",
                    "unit_price", "unit_cost", "voided_at")
    list_filter = ("invoice_kind",)
    search_fields = ("product__name",)
    ordering = ("-voided_at",)
    readonly_fields = ("voided_at",)