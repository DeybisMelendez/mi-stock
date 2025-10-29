from django import forms
from .models import Category, Product, Purchase, Sale


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "stock", "price", "average_cost"]


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["supplier", "product", "quantity", "cost"]


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["customer", "product", "quantity"]
