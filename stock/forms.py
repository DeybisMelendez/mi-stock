from django import forms
from .models import (
    Category, ExpenseCategory, Product, ProductImage,
    Purchase, Sale, Expense,
    PurchaseInvoice, SaleInvoice,
    OtherIncomeCategory, OtherIncome,
    Department, Customer,
    Tag,
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["name"]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description",
                  "stock", "price", "average_cost", "active", "tags"]


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


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "whatsapp", "address", "department", "notes", "active"]
        widgets = {
            "whatsapp": forms.TextInput(attrs={"type": "tel", "placeholder": "+505 8888 8888"}),
        }


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(active=True)


# ===== Facturas de venta =====
class SaleInvoiceForm(forms.ModelForm):
    class Meta:
        model = SaleInvoice
        fields = ["date", "customer_obj"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer_obj"].queryset = Customer.objects.filter(active=True).order_by("name")
        self.fields["customer_obj"].label_from_instance = lambda obj: obj.name


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["product", "quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(active=True)