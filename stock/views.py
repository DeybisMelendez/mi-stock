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
    context = {
        "title": "Categorías",
        "create_url": reverse("category_create"),
        "edit_url": "category_edit",
        "columns": ["id", "name"],
        "items": categories,
    }
    return render(request, "list.html", context)


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


def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect("category_list")
    else:
        form = CategoryForm(instance=category)

    context = {
        "title": "Editar categoría",
        "form": form,
    }
    return render(request, "form.html", context)


def product_list(request):
    products = Product.objects.filter(
        stock__gt=0).order_by("name", "-stock", "price")
    context = {
        "title": "Productos",
        "create_url": reverse("product_create"),
        "edit_url": "product_edit",
        "columns": ["id", "name", "category", "stock", "price", "average_cost"],
        "items": products,
    }
    return render(request, "list.html", context)


def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)

    context = {
        "title": "Editar producto",
        "form": form,
    }
    return render(request, "form.html", context)


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


def purchase_list(request):
    purchases = Purchase.objects.select_related(
        'product').all().order_by("-date")
    context = {
        "title": "Compras",
        "create_url": reverse("purchase_create"),
        "edit_url": "purchase_edit",
        "columns": ["date", "supplier", "product", "quantity", "cost"],
        "items": purchases,
    }
    return render(request, "list.html", context)


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


def purchase_edit(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)

    if request.method == "POST":
        form = PurchaseForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Compra actualizada correctamente.")
            return redirect("purchase_list")
    else:
        form = PurchaseForm(instance=purchase)

    context = {
        "title": "Editar compra",
        "form": form,
    }
    return render(request, "form.html", context)


def sale_list(request):
    sales = Sale.objects.select_related('product').all().order_by("-date")
    context = {
        "title": "Ventas",
        "create_url": reverse("sale_create"),
        "edit_url": "sale_edit",
        "columns": ["created_at", "customer", "product", "quantity", "price", "cost"],
        "items": sales,
    }
    return render(request, "list.html", context)


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


def sale_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)

    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, "Compra actualizada correctamente.")
            return redirect("sale_list")
    else:
        form = SaleForm(instance=sale)

    context = {
        "title": "Editar venta",
        "form": form,
    }
    return render(request, "form.html", context)
