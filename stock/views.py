from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .models import Product, Purchase, Sale
from django.contrib import messages

# ---------- PRODUCT VIEWS ----------


def product_list(request):
    products = Product.objects.all().order_by("category__name", "name")
    total_inventory = sum([p.average_cost * p.stock for p in products])
    context = {
        "products": products,
        "total_inventory": total_inventory
    }
    return render(request, "product_list.html", context)


@require_http_methods(["POST"])
def product_create(request):
    name = request.POST.get("name")
    description = request.POST.get("description")
    category = request.POST.get("category")
    stock = request.POST.get("stock")
    price = request.POST.get("price")
    if name and category and stock and description and price:
        Product.objects.create(
            name=name,
            category=category,
            stock=stock,
            description=description,
            price=price
        )
    messages.add_message(request, messages.INFO, "Hello world.")
    return redirect("product_list")
