from django import forms
from .models import (
    Category, ExpenseCategory, Product, ProductImage,
    Purchase, Sale, Expense,
    PurchaseInvoice, SaleInvoice,
    OtherIncomeCategory, OtherIncome,
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["name"]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "brand", "description",
                  "stock", "price", "average_cost"]


# Formset para gestionar múltiples fotos de un producto
ProductImageFormSet = forms.inlineformset_factory(
    Product, ProductImage,
    fields=["image"],
    extra=1, can_delete=True,
)


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["date", "category", "amount", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class OtherIncomeCategoryForm(forms.ModelForm):
    class Meta:
        model = OtherIncomeCategory
        fields = ["name"]


class OtherIncomeForm(forms.ModelForm):
    class Meta:
        model = OtherIncome
        fields = ["date", "category", "amount", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


# ===== Facturas de compra =====
class PurchaseInvoiceForm(forms.ModelForm):
    class Meta:
        model = PurchaseInvoice
        fields = ["date", "supplier"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["product", "quantity", "cost"]


# ===== Facturas de venta =====
class SaleInvoiceForm(forms.ModelForm):
    class Meta:
        model = SaleInvoice
        fields = ["date", "customer"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["product", "quantity"]