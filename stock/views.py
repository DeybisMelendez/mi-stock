from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .models import *
from django.contrib import messages
import datetime

# ---------- PRODUCT VIEWS ----------


def product_list(request):
    products = Product.objects.all().order_by("category__name", "name")
    total_inventory = sum([p.average_cost * p.stock for p in products])
    actual_month = datetime.date.today().month
    purchases = Purchase.objects.filter(created_at__month=actual_month)
    sales = Sale.objects.filter(created_at__month=actual_month)
    context = {
        "products": products,
        "total_inventory": total_inventory,
        "categories": Category.objects.all(),
        "purchases": sum([p.cost * p.quantity for p in purchases]),
        "sales": sum([p.price * p.quantity for p in sales]),
        "expenses": sum([p.cost * p.quantity for p in sales]),
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
