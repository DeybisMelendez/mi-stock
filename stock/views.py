from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import Category, Product, Purchase, Sale
from .forms import CategoryForm, ProductForm, PurchaseForm, SaleForm


def home(request):
    products = Product.objects.filter(stock__gt=0).select_related(
        'category').order_by("name", "category", "stock")
    return render(request, "home.html", {"products": products})


def category_list(request):
    categories = Category.objects.all().order_by("name")
    return render(request, "category_list.html", {"categories": categories})


def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada correctamente.")
            return redirect("category_list")
    else:
        form = CategoryForm()
    context = {
        "title": "Crear categoría",
        "form": form,
    }
    return render(request, "form.html", context)


# ---- PRODUCT ----
def product_list(request):
    products = Product.objects.select_related('category').filter(stock__gt=0)
    return render(request, "product_list.html", {"products": products})


def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto agregado correctamente.")
            return redirect("product_list")
    else:
        form = ProductForm()
    context = {
        "title": "Crear categoría",
        "form": form,
    }
    return render(request, "form.html", context)


# ---- PURCHASE ----
def purchase_list(request):
    purchases = Purchase.objects.select_related(
        'product').all().order_by("-date")
    return render(request, "purchase_list.html", {"purchases": purchases})


def purchase_create(request):
    if request.method == "POST":
        form = PurchaseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compra registrada correctamente.")
            return redirect("purchase_list")
    else:
        form = PurchaseForm()
    context = {
        "title": "Crear compra",
        "form": form,
    }
    return render(request, "form.html", context)


# ---- SALE ----
def sale_list(request):
    sales = Sale.objects.select_related('product').all().order_by("-date")
    return render(request, "sale_list.html", {"sales": sales})


def sale_create(request):
    if request.method == "POST":
        form = SaleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Venta registrada correctamente.")
            return redirect("sale_list")
    else:
        form = SaleForm()
    context = {
        "title": "Nueva venta",
        "form": form,
    }
    return render(request, "form.html", context)
