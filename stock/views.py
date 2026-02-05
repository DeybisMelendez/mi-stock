from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
import json
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.core import serializers


@login_required
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


@login_required
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


@login_required
def home(request):
    today = now()
    
    # Definir períodos de tiempo
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=7)
    last_week_start = today_start - timedelta(days=14)
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    last30 = today - timedelta(days=30)
    last365 = today - timedelta(days=365)
    
    # ===== INGRESOS POR PERÍODO =====
    # Hoy
    income_today = Sale.objects.filter(
        date__gte=today_start
    ).aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
    
    # Ayer
    income_yesterday = Sale.objects.filter(
        date__gte=yesterday_start, date__lt=today_start
    ).aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
    
    # Últimos 7 días
    income_last_7_days = Sale.objects.filter(
        date__gte=week_start
    ).aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
    
    # Semana anterior (hace 8-14 días)
    income_previous_week = Sale.objects.filter(
        date__gte=last_week_start, date__lt=week_start
    ).aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
    
    # Mes actual
    income_this_month = Sale.objects.filter(
        date__gte=month_start
    ).aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
    
    # Mes anterior
    income_last_month = Sale.objects.filter(
        date__gte=prev_month_start, date__lte=prev_month_end
    ).aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
    
    # Últimos 30 días
    income_last_30_days = Sale.objects.filter(
        date__gte=last30
    ).aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
    
    # Total histórico
    income_total = Sale.objects.aggregate(
        total=Sum(F("quantity") * F("price"))
    )["total"] or 0
    
    # ===== CÁLCULO DE PORCENTAJES DE CRECIMIENTO =====
    def growth_percentage(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100
    
    growth_today = growth_percentage(income_today, income_yesterday)
    growth_week = growth_percentage(income_last_7_days, income_previous_week)
    growth_month = growth_percentage(income_this_month, income_last_month)
    
    # ===== COMPRAS Y GASTOS =====
    # Compras mes actual
    purchases_this_month = Purchase.objects.filter(created_at__gte=month_start).aggregate(total=Sum(F("quantity") * F("cost")))["total"] or 0
    
    # Compras mes anterior
    purchases_last_month = Purchase.objects.filter(created_at__gte=prev_month_start, created_at__lte=prev_month_end).aggregate(total=Sum(F("quantity") * F("cost")))["total"] or 0
    
    # Compras últimos 30 días
    purchases_last_30_days = Purchase.objects.filter(created_at__gte=last30).aggregate(total=Sum(F("quantity") * F("cost")))["total"] or 0
    
    # Gastos mes actual
    expenses_this_month = Expense.objects.filter(date__gte=month_start).aggregate(total=Sum("amount"))["total"] or 0
    
    # Gastos mes anterior
    expenses_last_month = Expense.objects.filter(date__gte=prev_month_start, date__lte=prev_month_end).aggregate(total=Sum("amount"))["total"] or 0
    
    # Cálculo de crecimiento
    purchases_growth = growth_percentage(purchases_this_month, purchases_last_month)
    expenses_growth = growth_percentage(expenses_this_month, expenses_last_month)
    
    # ===== VENTAS (CANTIDAD) POR PERÍODO =====
    sales_count_today = Sale.objects.filter(date__gte=today_start).count()
    sales_count_last_7_days = Sale.objects.filter(date__gte=week_start).count()
    sales_count_total = Sale.objects.count()
    
    # ===== MÁRGENES Y COSTOS =====
    # Margen bruto últimos 30 días
    margin_last_30_days = Sale.objects.filter(
        date__gte=last30
    ).aggregate(m=Sum((F("price") - F("cost")) * F("quantity")))["m"] or 0
    
    # Margen bruto total
    margin_total = Sale.objects.aggregate(
        m=Sum((F("price") - F("cost")) * F("quantity"))
    )["m"] or 0
    
    # Gastos últimos 30 días
    expenses_last_30_days = Expense.objects.filter(
        date__gte=last30
    ).aggregate(total=Sum("amount"))["total"] or 0
    
    # ===== INVENTARIO =====
    # Valor del inventario actual
    inventory_value = Product.objects.annotate(
        value=F("stock") * F("average_cost")
    ).aggregate(total=Sum("value"))["total"] or 0
    
    # Productos con bajo stock (< 2 unidades)
    low_stock = Product.objects.filter(stock__lt=2).order_by("stock")[:10]
    
    # Productos sin stock
    out_of_stock = Product.objects.filter(stock=0).order_by("name")[:10]
    
    # ===== TOP PRODUCTOS =====
    # Hoy
    top_products_today = (
        Sale.objects.filter(date__gte=today_start)
        .values("product__name")
        .annotate(total_sold=Sum("quantity"), total_revenue=Sum(F("quantity") * F("price")))
        .order_by("-total_sold")[:5]
    )
    
    # Últimos 7 días
    top_products_week = (
        Sale.objects.filter(date__gte=week_start)
        .values("product__name")
        .annotate(total_sold=Sum("quantity"), total_revenue=Sum(F("quantity") * F("price")))
        .order_by("-total_sold")[:5]
    )
    
    # Últimos 30 días
    top_products_month = (
        Sale.objects.filter(date__gte=last30)
        .values("product__name")
        .annotate(total_sold=Sum("quantity"), total_revenue=Sum(F("quantity") * F("price")))
        .order_by("-total_sold")[:5]
    )
    
    # ===== TOP CATEGORÍAS =====
    top_categories_month = (
        Sale.objects.filter(date__gte=last30)
        .values("product__category__name")
        .annotate(total_sold=Sum("quantity"), total_revenue=Sum(F("quantity") * F("price")))
        .order_by("-total_sold")[:5]
    )
    
    # ===== PROYECCIÓN DE INVENTARIO =====
    products_with_stock = Product.objects.filter(stock__gt=0)
    projection_rows = []
    
    for p in products_with_stock:
        sold_365 = Sale.objects.filter(
            product=p, date__gte=last365
        ).aggregate(total=Sum("quantity"))["total"] or 0
        
        if sold_365 > 0:
            days_per_unit = 365 / sold_365
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
    
    # Ordenar por los que se agotan antes
    business_projection = sorted(
        [row for row in projection_rows if row["days_to_runout"] is not None],
        key=lambda r: r["days_to_runout"]
    )[:5]
    
    # ===== DATOS PARA GRÁFICOS =====
    # Ventas de los últimos 7 días (para gráfico de línea)
    daily_sales_data = []
    daily_sales_labels = []
    daily_sales_values = []
    for i in range(7):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        day_income = Sale.objects.filter(
            date__gte=day_start, date__lt=day_end
        ).aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0
        # Convertir a float para JSON
        day_income_float = float(day_income)
        daily_sales_data.insert(0, {
            "date": day_start.strftime("%a %d"),
            "income": day_income_float
        })
        daily_sales_labels.insert(0, day_start.strftime("%a %d"))
        daily_sales_values.insert(0, day_income_float)
    
    # Ventas por categoría últimos 30 días (para gráfico de torta)
    category_data = []
    category_labels = []
    category_values = []
    for cat in top_categories_month:
        category_name = cat["product__category__name"] or "Sin categoría"
        revenue = cat["total_revenue"]
        # Convertir a float para JSON
        revenue_float = float(revenue)
        category_data.append({
            "category": category_name,
            "revenue": revenue_float
        })
        category_labels.append(category_name)
        category_values.append(revenue_float)
    
    # Convertir a JSON para uso en templates
    daily_sales_labels_json = json.dumps(daily_sales_labels)
    daily_sales_values_json = json.dumps(daily_sales_values)
    category_labels_json = json.dumps(category_labels)
    category_values_json = json.dumps(category_values)
    

    
    # ===== PREPARAR CONTEXTO =====
    context = {
        # Períodos
        "today": today.date(),
        "week_start": week_start.date(),
        "month_start": month_start.date(),
        
        # Ingresos
        "income_today": income_today,
        "income_yesterday": income_yesterday,
        "income_last_7_days": income_last_7_days,
        "income_previous_week": income_previous_week,
        "income_this_month": income_this_month,
        "income_last_month": income_last_month,
        "income_last_30_days": income_last_30_days,
        "income_total": income_total,
        
        # Crecimiento
        "growth_today": growth_today,
        "growth_week": growth_week,
        "growth_month": growth_month,
        
        # Ventas (cantidad)
        "sales_count_today": sales_count_today,
        "sales_count_last_7_days": sales_count_last_7_days,
        "sales_count_total": sales_count_total,
        
        # Margenes y gastos
        "margin_last_30_days": margin_last_30_days,
        "margin_total": margin_total,
        "expenses_last_30_days": expenses_last_30_days,
        "expenses_this_month": expenses_this_month,
        "expenses_last_month": expenses_last_month,
        "expenses_growth": expenses_growth,
        "purchases_this_month": purchases_this_month,
        "purchases_last_month": purchases_last_month,
        "purchases_last_30_days": purchases_last_30_days,
        "purchases_growth": purchases_growth,
        
        # Inventario
        "inventory_value": inventory_value,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        
        # Top productos
        "top_products_today": top_products_today,
        "top_products_week": top_products_week,
        "top_products_month": top_products_month,
        
        # Top categorías
        "top_categories_month": top_categories_month,
        
        # Proyección
        "business_projection": business_projection,
        
        # Datos para gráficos
        "daily_sales_data": daily_sales_data,
        "category_data": category_data,
        "daily_sales_labels_json": daily_sales_labels_json,
        "daily_sales_values_json": daily_sales_values_json,
        "category_labels_json": category_labels_json,
        "category_values_json": category_values_json,
    }
    
    return render(request, "home.html", context)


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


@login_required
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


@login_required
def user_profile(request):
    return render(request, "user_profile.html", {
        "user": request.user
    })

@login_required
def export_data(request):
    from datetime import datetime
    
    models_to_export = ["Category", "Product", "Purchase", "Sale", "Expense"]
    data = {
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "version": "1.0",
            "model_count": len(models_to_export),
        },
        "data": {}
    }
    
    for model_name in models_to_export:
        model = apps.get_model("stock", model_name)
        queryset = model.objects.all()
        # Use Django's JSON serializer which handles Decimal, datetime, etc.
        serialized_json = serializers.serialize("json", queryset)
        serialized_data = json.loads(serialized_json)
        data["data"][model_name] = serialized_data
    
    response = HttpResponse(json.dumps(data, indent=2, ensure_ascii=False), content_type="application/json")
    response["Content-Disposition"] = 'attachment; filename="mi-stock-backup-{}.json"'.format(datetime.now().strftime("%Y%m%d-%H%M%S"))
    return response

@login_required
def import_data(request):
    if request.method == "POST" and request.FILES.get("backup_file"):
        uploaded_file = request.FILES["backup_file"]
        try:
            content = uploaded_file.read().decode("utf-8")
            data = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            messages.error(request, f"Error al leer el archivo: {e}")
            return redirect("home")
        
        # Importar en orden para respetar dependencias
        models_order = ["Category", "Product", "Purchase", "Sale", "Expense"]
        imported_counts = {}
        
        for model_name in models_order:
            if model_name not in data.get("data", {}):
                continue
            serialized_list = data["data"][model_name]
            # Convertir la lista de dicts a JSON string para deserialización
            json_str = json.dumps(serialized_list)
            imported = 0
            for obj in serializers.deserialize("json", json_str):
                obj.save()
                imported += 1
            imported_counts[model_name] = imported
        
        messages.success(request, f"Datos importados exitosamente: {imported_counts}")
        return redirect("home")
    
    # Si no es POST, mostrar formulario
    return render(request, "import_form.html")
