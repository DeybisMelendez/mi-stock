from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import Category, Product, Purchase, Sale
from .forms import CategoryForm, ProductForm, PurchaseForm, SaleForm
from django.apps import apps


def generic_list_view(request, model_str):
    model = apps.get_model("stock", model_str.capitalize())
    items = model.objects.all()
    context = {}

    match model_str:
        case "category":
            context = {
                "model": model_str,
                "items": items,
                "title": "Categoría",
                "fields": ["Nombre"],
                "columns": ["name"],
            }
        case "product":
            context = {
                "model": model_str,
                "items": items,
                "title": "Productos",
                "fields": ["Nombre", "Categoría", "Stock", "Precio", "Costo Promedio"],
                "columns": ["name", "category", "stock", "price", "average_cost"],
            }
        case "sale":
            context = {
                "model": model_str,
                "items": items,
                "title": "Ventas",
                "fields": ["Fecha", "Producto", "Cantidad", "Precio", "Costo"],
                "columns": ["created_at", "product", "quantity", "price", "cost"],
            }
        case "purchase":
            context = {
                "model": model_str,
                "items": items,
                "title": "Compras",
                "fields": ["Fecha", "Producto", "Cantidad", "Costo"],
                "columns": ["created_at", "product", "quantity", "cost"],
            }

    return render(request, "list.html", context)


def generic_form_view(request, model_str, pk=None):
    model = apps.get_model("stock", model_str.capitalize())
    obj = get_object_or_404(model, pk=pk) if pk else None
    title = "Editar " if obj else "Agregar nueva "
    form_class = None
    match model_str:
        case "category":
            form_class = CategoryForm
            title += "Categoría"
        case "product":
            form_class = ProductForm
            title += "Producto"
        case "sale":
            form_class = SaleForm
            title += "Venta"
        case "purchase":
            form_class = PurchaseForm
            title += "Compra"

    if request.method == "POST":
        form = form_class(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} guardado correctamente.")
            return redirect(success_url)
    else:
        form = form_class(instance=obj)

    context = {
        "title": title,
        "form": form,
    }
    return render(request, "form.html", context)


def home(request):
    products = Product.objects.filter(stock__gt=0).select_related(
        'category').order_by("name", "category", "stock")
    return render(request, "home.html", {"products": products})
