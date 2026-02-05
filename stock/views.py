from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import Category, Product, Purchase, Sale, Expense
from .forms import CategoryForm, ProductForm, PurchaseForm, SaleForm, ExpenseForm
from django.apps import apps
from django.db.models import Q
from django.db.models import (
    CharField, TextField, EmailField, SlugField, UUIDField
)
from django.db.models import Sum, Count, Avg, F
from django.utils.timezone import now
from datetime import timedelta, date
from django.core.paginator import Paginator


def generic_list_view(request, model_str):
    model = apps.get_model("stock", model_str.capitalize())
    queryset = model.objects.all()

    fields = []
    columns = []
    title = ""

    match model_str:
        case "category":
            fields = ["Nombre"]
            columns = ["name"]
            title = "Categoría"

        case "product":
            fields = ["Nombre", "Categoría",
                      "Stock", "Precio", "Costo Promedio"]
            columns = ["name", "category__name",
                       "stock", "price", "average_cost"]
            title = "Productos"

        case "sale":
            fields = ["Fecha", "Producto", "Cantidad", "Precio", "Costo"]
            columns = ["created_at", "product__name",
                       "quantity", "price", "cost"]
            title = "Ventas"

        case "purchase":
            fields = ["Fecha", "Producto", "Cantidad", "Costo"]
            columns = ["created_at", "product__name", "quantity", "cost"]
            title = "Compras"

        case "expense":
            fields = ["Fecha", "Descripción", "Monto"]
            columns = ["created_at", "description", "amount"]
            title = "Gastos"

    context = {
        "model": model_str,
        "title": title,
        "fields": fields,
        "columns": columns,
        "page_obj": queryset,
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
        case "expense":
            form_class = ExpenseForm
            title += "Gasto"

    if request.method == "POST":
        form = form_class(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"Se ha guardado correctamente.")
            return redirect("new", model_str=model_str)
    else:
        form = form_class(instance=obj)

    context = {
        "title": title,
        "form": form,
    }
    return render(request, "form.html", context)


def home(request):
    products = Product.objects.filter(stock__gt=0).select_related('category')

    today = now()
    last30 = today - timedelta(days=30)
    last365 = today - timedelta(days=365)

    # ventas → top global
    top_products = (
        Sale.objects.values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:10]
    )

    # top 30 days
    top_products_30 = (
        Sale.objects.filter(date__gte=last30)
        .values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    # ingresos generales
    total_income = Sale.objects.aggregate(
        total=Sum(F("quantity") * F("price"))
    )["total"] or 0

    # ingresos últimos 30 días
    total_income_30 = Sale.objects.filter(date__gte=last30).aggregate(
        total=Sum(F("quantity") * F("price"))
    )["total"] or 0

    total_sales_count = Sale.objects.count()

    # valor inventario actual
    inventory_value = (
        Product.objects.annotate(value=F("stock") * F("average_cost"))
        .aggregate(total=Sum("value"))["total"] or 0
    )

    # promedio ticket
    avg_ticket = Sale.objects.aggregate(
        avg=Avg(F("quantity") * F("price"))
    )["avg"] or 0

    # margen bruto total real
    margin_gross_total = (
        Sale.objects.aggregate(
            m=Sum((F("price") - F("cost")) * F("quantity"))
        )["m"] or 0
    )

    # top categorías vendidas
    top_categories = (
        Sale.objects
        .values("product__category__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    # mes actual
    month_start = today.replace(day=1)
    this_month_income = (
        Sale.objects.filter(date__gte=month_start)
        .aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
    )

    # mes anterior
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    last_month_income = (
        Sale.objects
        .filter(date__gte=prev_month_start, date__lte=prev_month_end)
        .aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
    )

    # productos con bajo stock
    low_stock = Product.objects.filter(stock__lt=2).order_by("stock")[:10]

    projection_rows = []

    for p in products:
        sold_365 = (
            Sale.objects
            .filter(product=p, date__gte=last365)
            .aggregate(total=Sum("quantity"))
        )["total"] or 0

        if sold_365 > 0:
            # cada cuántos días vendo una unidad en promedio
            days_per_unit = 365 / sold_365
            # en cuántos días me quedo sin stock si sigo ese ritmo
            days_to_runout = p.stock * days_per_unit
        else:
            days_per_unit = None
            days_to_runout = None

        projection_rows.append({
            "product": p,
            "sold_365": sold_365,
            "days_per_unit": days_per_unit,
            "days_to_runout": days_to_runout,
        })

    # ordenamos por los que se agotan antes
    business_projection = sorted(
        [row for row in projection_rows if row["days_to_runout"] is not None],
        key=lambda r: r["days_to_runout"]
    )[:10]

    return render(
        request,
        "home.html",
        {
            "products": products,
            "top_products": top_products,
            "top_products_30": top_products_30,
            "top_categories": top_categories,
            "total_income": total_income,
            "total_income_30": total_income_30,
            "total_sales_count": total_sales_count,
            "inventory_value": inventory_value,
            "avg_ticket": avg_ticket,
            "margin_gross_total": margin_gross_total,
            "this_month_income": this_month_income,
            "last_month_income": last_month_income,
            "low_stock": low_stock,
            "business_projection": business_projection,
        },
    )


def month_range_from_offset(month_offset):
    today = now().date()

    # mes actual menos offset
    year = today.year
    month = today.month - month_offset

    while month <= 0:
        month += 12
        year -= 1

    first_day = date(year, month, 1)

    # último día del mes
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    return first_day, last_day


def month_result(request, month_offset=0):

    start, end = month_range_from_offset(month_offset)

    # ingresos del mes
    income = (
        Sale.objects.filter(date__date__range=[start, end])
        .aggregate(total=Sum(F("quantity") * F("price")))
    )["total"] or 0

    # costo del mes
    costs = (
        Sale.objects.filter(date__date__range=[start, end])
        .aggregate(total=Sum(F("quantity") * F("cost")))
    )["total"] or 0

    # gastos operativos del mes
    expenses = (
        Expense.objects.filter(date__date__range=[start, end])
        .aggregate(total=Sum("amount"))
    )["total"] or 0

    # utilidad bruta
    gross_profit = income - costs

    # utilidad neta
    net_profit = income - costs - expenses

    return render(request, "month_result.html", {
        "start": start,
        "end": end,
        "offset": month_offset,

        "income": income,
        "costs": costs,
        "expenses": expenses,

        "gross_profit": gross_profit,
        "net_profit": net_profit,
    })
