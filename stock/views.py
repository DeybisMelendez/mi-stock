from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import (
    Category, ExpenseCategory, Product, ProductImage,
    Purchase, Sale, Expense,
    PurchaseInvoice, SaleInvoice,
    OtherIncomeCategory, OtherIncome,
    Department, Customer,
    Tag,
)
from .forms import (
    CategoryForm, ExpenseCategoryForm, ProductForm, ExpenseForm,
    PurchaseInvoiceForm, PurchaseItemForm,
    SaleInvoiceForm, SaleItemForm,
    ProductImageFormSet,
    OtherIncomeCategoryForm, OtherIncomeForm,
    CustomerForm,
    TagForm,
)
from django.apps import apps
from django.db.models import Sum, F, Max
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from datetime import timedelta, date
import json
from django.http import HttpResponse, Http404
from django.core import serializers


# Mapeo de model_str → nombre de modelo real (para apps.get_model)
MODEL_NAME_MAP = {
    "purchase": "PurchaseInvoice",
    "sale": "SaleInvoice",
    "expensecategory": "ExpenseCategory",
    "otherincome": "OtherIncome",
    "otherincomecategory": "OtherIncomeCategory",
    "tag": "Tag",
}


@login_required
def generic_list_view(request, model_str):
    valid_models = {"category", "product", "sale", "purchase", "expense",
                    "expensecategory", "otherincome", "otherincomecategory",
                    "customer", "tag"}
    if model_str not in valid_models:
        raise Http404

    model_name = MODEL_NAME_MAP.get(model_str, model_str.capitalize())
    try:
        model = apps.get_model("stock", model_name)
    except LookupError:
        raise Http404

    # Compras y ventas usan facturas con varias líneas
    if model_str in ("purchase", "sale"):
        tag_id = request.GET.get("tag")
        selected_tag = None
        if tag_id and tag_id.isdigit():
            selected_tag = Tag.objects.filter(pk=int(tag_id)).first()
        invoices = model.objects.select_related("customer_obj").all()
        if selected_tag:
            invoices = invoices.filter(items__product__tags=selected_tag).distinct()
        rows = []
        for inv in invoices:
            rows.append({
                "id": inv.id,
                "date": inv.date,
                "party": inv.supplier if model_str == "purchase" else inv.customer_obj.name,
                "items_summary": ", ".join(
                    f"{i.quantity} × {i.product.name}"
                    for i in inv.items.all()
                ),
                "total": inv.get_total(),
            })
        if model_str == "purchase":
            fields = ["Fecha", "Proveedor", "Productos", "Total"]
            columns = ["date", "party", "items_summary", "total"]
            title = "Compras"
        else:
            fields = ["Fecha", "Cliente", "Productos", "Total"]
            columns = ["date", "party", "items_summary", "total"]
            title = "Ventas"
        available_tags = list(Tag.objects.all().values("id", "name"))
        context = {
            "model": model_str,
            "title": title,
            "fields": fields,
            "columns": columns,
            "page_obj": rows,
            "available_tags": available_tags,
            "selected_tag": selected_tag,
            "tag_filter_url_key": "tag",
        }
        return render(request, "list.html", context)

    fields = []
    columns = []
    title = ""

    match model_str:
        case "category":
            fields = ["Nombre"]
            columns = ["name"]
            title = "Categorías"
            queryset = model.objects.all()
            page_obj = queryset

        case "expensecategory":
            fields = ["Nombre"]
            columns = ["name"]
            title = "Categorías de Gastos"
            queryset = model.objects.all()
            page_obj = queryset

        case "otherincomecategory":
            fields = ["Nombre"]
            columns = ["name"]
            title = "Categorías de Otros Ingresos"
            queryset = model.objects.all()
            page_obj = queryset

        case "product":
            tab = request.GET.get("tab", "active")
            if tab not in ("active", "inactive"):
                tab = "active"
            tag_id = request.GET.get("tag")
            selected_tag = None
            if tag_id and tag_id.isdigit():
                selected_tag = Tag.objects.filter(pk=int(tag_id)).first()

            active_qs = Product.objects.filter(active=True).select_related("category").prefetch_related("tags")
            inactive_qs = Product.objects.filter(active=False).select_related("category").prefetch_related("tags")
            if selected_tag:
                active_qs = active_qs.filter(tags=selected_tag)
                inactive_qs = inactive_qs.filter(tags=selected_tag)
            fields = ["Nombre", "Categoría",
                      "Etiquetas", "Stock", "Precio", "Costo Promedio"]
            columns = ["name", "category__name",
                       "tags", "stock", "price", "average_cost"]
            title = "Productos"

            def _serialize(qs):
                rows = []
                for p in qs:
                    row = []
                    for col in columns:
                        if col == "tags":
                            row.append(", ".join(
                                t.name for t in p.tags.all()
                            ))
                            continue
                        val = p
                        for part in col.split("__"):
                            val = getattr(val, part, None) if val is not None else None
                            if val is None:
                                break
                        if hasattr(val, "strftime"):
                            val = val.strftime("%d/%m/%Y")
                        row.append("" if val is None else str(val))
                    edit_url   = reverse("product_edit",   args=[p.id])
                    detail_url = reverse("product_detail", args=[p.id])
                    toggle_url = reverse("product_toggle_active", args=[p.id])
                    actions = json.dumps({
                        "detail": detail_url,
                        "edit": edit_url,
                        "toggle": toggle_url,
                        "active": p.active,
                        "next": request.get_full_path(),
                    })
                    row.append(actions)
                    rows.append(row)
                return rows

            available_tags = list(Tag.objects.all().values("id", "name"))

            return render(request, "list.html", {
                "model": model_str,
                "title": title,
                "fields": fields,
                "columns": columns,
                "active_count": active_qs.count(),
                "inactive_count": inactive_qs.count(),
                "active_data_json": json.dumps(_serialize(active_qs)),
                "inactive_data_json": json.dumps(_serialize(inactive_qs)),
                "tab": tab,
                "available_tags": available_tags,
                "selected_tag": selected_tag,
                "tag_filter_url_key": "tag",
                "current_full_path": request.get_full_path(),
            })

        case "expense":
            queryset = model.objects.all().select_related("category")
            fields = ["Fecha", "Categoría", "Descripción", "Monto"]
            columns = ["date", "category__name", "description", "amount"]
            title = "Gastos"
            page_obj = queryset

        case "otherincome":
            queryset = model.objects.all().select_related("category")
            fields = ["Fecha", "Categoría", "Descripción", "Monto"]
            columns = ["date", "category__name", "description", "amount"]
            title = "Otros Ingresos"
            page_obj = queryset

        case "customer":
            queryset = model.objects.all().select_related("department")
            fields = ["Nombre", "WhatsApp", "Departamento", "Activo"]
            columns = ["name", "whatsapp", "department__name", "active"]
            title = "Clientes"
            page_obj = queryset

        case "tag":
            queryset = model.objects.all()
            fields = ["Nombre"]
            columns = ["name"]
            title = "Etiquetas"
            page_obj = queryset

    context = {
        "model": model_str,
        "title": title,
        "fields": fields,
        "columns": columns,
        "page_obj": page_obj,
    }
    return render(request, "list.html", context)


@login_required
def generic_form_view(request, model_str, pk=None):
    valid_models = {"category", "expense", "expensecategory",
                    "otherincome", "otherincomecategory", "customer", "tag"}
    if model_str not in valid_models:
        raise Http404

    model_name = MODEL_NAME_MAP.get(model_str, model_str.capitalize())
    try:
        model = apps.get_model("stock", model_name)
    except LookupError:
        raise Http404

    obj = get_object_or_404(model, pk=pk) if pk else None
    title = "Editar " if obj else "Agregar nueva "
    form_class = None
    match model_str:
        case "category":
            form_class = CategoryForm
            title += "Categoría"
        case "expensecategory":
            form_class = ExpenseCategoryForm
            title += "Categoría de Gasto"
        case "otherincomecategory":
            form_class = OtherIncomeCategoryForm
            title += "Categoría de Otro Ingreso"
        case "expense":
            form_class = ExpenseForm
            title += "Gasto"
        case "otherincome":
            form_class = OtherIncomeForm
            title += "Otro Ingreso"
        case "customer":
            form_class = CustomerForm
            title += "Cliente"
        case "tag":
            form_class = TagForm
            title += "Etiqueta"

    if request.method == "POST":
        form = form_class(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"Se ha guardado correctamente.")
            return redirect("list", model_str=model_str) if pk else redirect("new", model_str=model_str)
    else:
        form = form_class(instance=obj)

    context = {
        "title": title,
        "form": form,
    }
    return render(request, "form.html", context)


@login_required
def product_form_view(request, pk=None):
    """Vista dedicada para crear/editar productos con marca y múltiples fotos."""
    product = get_object_or_404(Product, pk=pk) if pk else None
    title = ("Editar " if product else "Agregar nuevo ") + "Producto"

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        formset = ProductImageFormSet(request.POST, request.FILES,
                                      instance=product)
        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.instance = product
            formset.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("product_detail", pk=product.id) if pk else redirect("product_new")
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product)

    context = {
        "title": title,
        "form": form,
        "formset": formset,
    }
    return render(request, "product_form.html", context)


@login_required
def product_detail_view(request, pk):
    """Vista de detalle de un producto con sus fotos descargables."""
    product = get_object_or_404(Product, pk=pk)

    sales_stats = Sale.objects.filter(product=product).aggregate(
        total_sold=Sum("quantity"),
        total_revenue=Sum(F("quantity") * F("price")),
        last_sale=Max("invoice__date"),
    )
    purchases_stats = Purchase.objects.filter(product=product).aggregate(
        total_bought=Sum("quantity"),
        total_spent=Sum(F("quantity") * F("cost")),
        last_purchase=Max("invoice__date"),
    )

    unit_margin = (product.price - product.average_cost) if product.average_cost else 0
    margin_pct = (
        (unit_margin / product.price * 100) if product.price else 0
    )

    context = {
        "title": f"{product.name}",
        "product": product,
        "edit_url": reverse("product_edit", args=[product.id]),
        "list_url": reverse("list", args=["product"]),
        "inventory_value": product.stock * product.average_cost,
        "unit_margin": unit_margin,
        "margin_pct": margin_pct,
        "total_sold": sales_stats["total_sold"] or 0,
        "total_revenue": sales_stats["total_revenue"] or 0,
        "last_sale": sales_stats["last_sale"],
        "total_bought": purchases_stats["total_bought"] or 0,
        "total_spent": purchases_stats["total_spent"] or 0,
        "last_purchase": purchases_stats["last_purchase"],
    }
    return render(request, "product_detail.html", context)


@login_required
@require_POST
def product_toggle_active(request, pk):
    """Activa o desactiva un producto desde la lista, preservando el contexto."""
    product = get_object_or_404(Product, pk=pk)
    product.active = not product.active
    product.save(update_fields=["active"])
    verb = "activado" if product.active else "desactivado"
    messages.success(request, f"Producto {verb} correctamente.")

    next_url = request.POST.get("next") or reverse("list", args=["product"])
    return redirect(next_url)


# ===== Vistas de facturas (compra/venta con múltiples líneas) =====
PurchaseItemFormSet = inlineformset_factory(
    PurchaseInvoice, Purchase, PurchaseItemForm,
    extra=1, can_delete=True,
)
SaleItemFormSet = inlineformset_factory(
    SaleInvoice, Sale, SaleItemForm,
    extra=1, can_delete=True,
)


@login_required
def purchase_invoice_form_view(request, pk=None):
    invoice = get_object_or_404(PurchaseInvoice, pk=pk) if pk else None
    title = ("Editar " if invoice else "Agregar nueva ") + "Factura de Compra"

    if request.method == "POST":
        form = PurchaseInvoiceForm(request.POST, instance=invoice)
        formset = PurchaseItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.instance = invoice
            formset.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("purchase_invoice_detail", pk=invoice.id) if pk else redirect("purchase_invoice_new")
    else:
        form = PurchaseInvoiceForm(instance=invoice)
        formset = PurchaseItemFormSet(instance=invoice)

    context = {
        "title": title,
        "form": form,
        "formset": formset,
        "kind": "purchase",
        "product_prices_json": json.dumps(
            {p.id: str(p.price) for p in Product.objects.filter(active=True)}
        ),
        "product_costs_json": json.dumps(
            {p.id: str(p.average_cost) for p in Product.objects.filter(active=True)}
        ),
        "product_stocks_json": json.dumps(
            {p.id: p.stock for p in Product.objects.filter(active=True)}
        ),
    }
    return render(request, "invoice_form.html", context)


@login_required
def sale_invoice_form_view(request, pk=None):
    invoice = get_object_or_404(SaleInvoice, pk=pk) if pk else None
    title = ("Editar " if invoice else "Agregar nueva ") + "Factura de Venta"

    if request.method == "POST":
        form = SaleInvoiceForm(request.POST, instance=invoice)
        formset = SaleItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.instance = invoice
            formset.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("sale_invoice_detail", pk=invoice.id) if pk else redirect("sale_invoice_new")
    else:
        form = SaleInvoiceForm(instance=invoice)
        formset = SaleItemFormSet(instance=invoice)

    context = {
        "title": title,
        "form": form,
        "formset": formset,
        "kind": "sale",
        "product_prices_json": json.dumps(
            {p.id: str(p.price) for p in Product.objects.filter(active=True)}
        ),
        "product_stocks_json": json.dumps(
            {p.id: p.stock for p in Product.objects.filter(active=True)}
        ),
    }
    return render(request, "invoice_form.html", context)


@login_required
def purchase_invoice_detail_view(request, pk):
    """Vista de detalle de una factura de compra."""
    invoice = get_object_or_404(PurchaseInvoice, pk=pk)
    context = {
        "title": f"Factura de Compra #{invoice.id}",
        "invoice": invoice,
        "party_label": "Proveedor",
        "party": invoice.supplier,
        "kind": "purchase",
        "edit_url": reverse("purchase_invoice_edit", args=[invoice.id]),
        "list_url": reverse("list", args=["purchase"]),
    }
    return render(request, "invoice_detail.html", context)


@login_required
def sale_invoice_detail_view(request, pk):
    """Vista de detalle de una factura de venta."""
    invoice = get_object_or_404(SaleInvoice, pk=pk)
    context = {
        "title": f"Factura de Venta #{invoice.id}",
        "invoice": invoice,
        "party_label": "Cliente",
        "party": invoice.customer_obj.name,
        "kind": "sale",
        "edit_url": reverse("sale_invoice_edit", args=[invoice.id]),
        "list_url": reverse("list", args=["sale"]),
    }
    return render(request, "invoice_detail.html", context)


def _top_products(since):
    """Top productos por ingresos desde la fecha dada."""
    rows = (
        Sale.objects.filter(invoice__date__gte=since)
        .values("product__name", "product__category__name")
        .annotate(
            total_sold=Sum("quantity"),
            total_revenue=Sum(F("quantity") * F("price")),
        )
        .order_by("-total_revenue")[:10]
    )
    total_revenue = sum(r["total_revenue"] for r in rows) or 0
    for r in rows:
        r["percentage"] = (r["total_revenue"] / total_revenue * 100) if total_revenue else 0
    return list(rows)


def _period_label(start, end):
    """Ej: 'Ene 2026', 'Ene – Jun 2026' o 'Ene 2025 – Jun 2026' según el rango."""
    if start.year != end.year:
        return f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}"
    if start.month != end.month:
        return f"{start.strftime('%b')} – {end.strftime('%b %Y')}"
    return f"{start.strftime('%b %Y')}"


@login_required
def home(request):
    today_date = now().date()

    # ===== PERÍODOS CALENDARIO =====
    month_start = today_date.replace(day=1)
    prev_month_end = month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    sem_start = today_date.replace(month=(7 if today_date.month > 6 else 1), day=1)
    year_start = today_date.replace(month=1, day=1)
    last30_date = today_date - timedelta(days=30)

    def growth_percentage(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100

    def sale_sum(start, end=None):
        qs = Sale.objects.filter(invoice__date__gte=start)
        if end:
            qs = qs.filter(invoice__date__lte=end)
        return qs.aggregate(total=Sum(F("quantity") * F("price")))["total"] or 0

    def cost_sum(start, end):
        return (
            Sale.objects.filter(invoice__date__range=[start, end])
            .aggregate(total=Sum(F("quantity") * F("cost")))["total"]
            or 0
        )

    # ===== INGRESOS Y COSTOS =====
    income_this_month = sale_sum(month_start, today_date)
    income_last_month = sale_sum(prev_month_start, prev_month_end)
    income_semester = sale_sum(sem_start, None)
    income_year = sale_sum(year_start, None)
    cost_this_month = cost_sum(month_start, today_date)

    # ===== GASTOS Y OTROS INGRESOS =====
    expenses_this_month = Expense.objects.filter(
        date__range=[month_start, today_date]
    ).aggregate(total=Sum("amount"))["total"] or 0
    expenses_last_month = Expense.objects.filter(
        date__gte=prev_month_start, date__lte=prev_month_end
    ).aggregate(total=Sum("amount"))["total"] or 0
    other_income_this_month = OtherIncome.objects.filter(
        date__range=[month_start, today_date]
    ).aggregate(total=Sum("amount"))["total"] or 0

    # ===== CLIENTES NUEVOS DEL MES =====
    new_customers_this_month = Customer.objects.filter(
        created_at__year=month_start.year,
        created_at__month=month_start.month,
    ).count()
    new_customers_last_month = Customer.objects.filter(
        created_at__year=prev_month_start.year,
        created_at__month=prev_month_start.month,
    ).count()

    # ===== GANANCIA DEL MES =====
    gross_profit_month = income_this_month - cost_this_month
    net_profit_month = (
        income_this_month + other_income_this_month
        - cost_this_month - expenses_this_month
    )
    gross_margin_pct = (gross_profit_month / income_this_month * 100) if income_this_month else 0
    net_margin_pct = (net_profit_month / income_this_month * 100) if income_this_month else 0

    # ===== INVENTARIO =====
    inventory_value = (
        Product.objects.annotate(value=F("stock") * F("average_cost"))
        .aggregate(total=Sum("value"))["total"] or 0
    )
    low_stock = Product.objects.filter(stock__gt=0, stock__lt=2).order_by("stock")
    out_of_stock = Product.objects.filter(stock=0).order_by("name")

    # ===== TOP PRODUCTOS (mes, semestre, año calendario) =====
    top_products_month = _top_products(month_start)
    top_products_semester = _top_products(sem_start)
    top_products_year = _top_products(year_start)

    # ===== TOP CATEGORÍAS (30 días) =====
    top_categories = (
        Sale.objects.filter(invoice__date__gte=last30_date)
        .values("product__category__name")
        .annotate(total_revenue=Sum(F("quantity") * F("price")))
        .order_by("-total_revenue")[:5]
    )

    # ===== TENDENCIA: INGRESOS POR MES (últimos 12 meses) =====
    twelve_months_ago = (today_date.replace(day=1) - timedelta(days=365)).replace(day=1)
    month_map = {
        m["month"]: float(m["total"])
        for m in (
            Sale.objects.filter(invoice__date__gte=twelve_months_ago)
            .annotate(month=TruncMonth("invoice__date"))
            .values("month")
            .annotate(total=Sum(F("quantity") * F("price")))
        )
    }

    monthly_labels = []
    monthly_values = []
    current = today_date.replace(day=1)
    for _ in range(12):
        monthly_labels.append(current.strftime("%b %y"))
        monthly_values.append(month_map.get(current, 0))
        current = (current - timedelta(days=1)).replace(day=1)
    monthly_labels.reverse()
    monthly_values.reverse()

    # ===== DATOS PARA GRÁFICOS =====
    category_labels = [c["product__category__name"] or "Sin categoría"
                       for c in top_categories]
    category_values = [float(c["total_revenue"]) for c in top_categories]

    context = {
        "today": today_date,
        "month_label": month_start.strftime("%B %Y").capitalize(),
        "semester_label": _period_label(sem_start, today_date),
        "year_label": str(year_start.year),

        "income_this_month": income_this_month,
        "income_last_month": income_last_month,
        "income_semester": income_semester,
        "income_year": income_year,
        "growth_month": growth_percentage(income_this_month, income_last_month),

        "gross_profit_month": gross_profit_month,
        "gross_margin_pct": gross_margin_pct,
        "net_profit_month": net_profit_month,
        "net_margin_pct": net_margin_pct,
        "other_income_this_month": other_income_this_month,
        "expenses_this_month": expenses_this_month,
        "expenses_growth": growth_percentage(expenses_this_month, expenses_last_month),

        "new_customers_this_month": new_customers_this_month,
        "new_customers_last_month": new_customers_last_month,
        "new_customers_growth": growth_percentage(new_customers_this_month, new_customers_last_month),

        "inventory_value": inventory_value,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,

        "top_products_month": top_products_month,
        "top_products_semester": top_products_semester,
        "top_products_year": top_products_year,
        "top_products": [
            ("mes", top_products_month, "mes"),
            ("semestre", top_products_semester, "semestre"),
            ("año", top_products_year, "año"),
        ],

        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_values_json": json.dumps(monthly_values),
        "category_labels_json": json.dumps(category_labels),
        "category_values_json": json.dumps(category_values),
    }

    return render(request, "home.html", context)


def month_range_from_offset(month_offset):
    today = now().date()

    year = today.year
    month = today.month - month_offset

    while month <= 0:
        month += 12
        year -= 1

    first_day = date(year, month, 1)

    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    return first_day, last_day


@login_required
def month_result(request, month_offset=0):

    start, end = month_range_from_offset(month_offset)

    sale_filter = {"invoice__date__range": [start, end]}
    date_filter = {"date__range": [start, end]}

    # Ingresos y costos del mes
    income = (
        Sale.objects.filter(**sale_filter)
        .aggregate(total=Sum(F("quantity") * F("price")))
    )["total"] or 0

    costs = (
        Sale.objects.filter(**sale_filter)
        .aggregate(total=Sum(F("quantity") * F("cost")))
    )["total"] or 0

    expenses = (
        Expense.objects.filter(**date_filter)
        .aggregate(total=Sum("amount"))
    )["total"] or 0

    other_income = (
        OtherIncome.objects.filter(**date_filter)
        .aggregate(total=Sum("amount"))
    )["total"] or 0

    gross_profit = income - costs
    net_profit = income + other_income - costs - expenses

    # Desglose por categoría de producto
    income_by_category = list(
        Sale.objects.filter(**sale_filter)
        .values("product__category__name")
        .annotate(
            income=Sum(F("quantity") * F("price")),
            cost=Sum(F("quantity") * F("cost")),
        )
        .order_by("-income")
    )
    for row in income_by_category:
        row["gross"] = (row["income"] or 0) - (row["cost"] or 0)

    # Gastos del mes: lista detallada y agrupada por categoría
    expenses_list = list(
        Expense.objects.filter(**date_filter).order_by("-date", "-id")
    )

    expenses_by_category = (
        Expense.objects.filter(**date_filter)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    # Otros ingresos del mes: lista detallada y agrupada por categoría
    other_income_list = list(
        OtherIncome.objects.filter(**date_filter).order_by("-date", "-id")
    )

    other_income_by_category = (
        OtherIncome.objects.filter(**date_filter)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    # Márgenes como porcentaje sobre los ingresos
    def pct(part, whole):
        if whole == 0:
            return 0
        return (part / whole) * 100

    gross_margin_pct = pct(gross_profit, income)
    net_margin_pct = pct(net_profit, income)
    costs_pct = pct(costs, income)
    expenses_pct = pct(expenses, income)
    other_income_pct = pct(other_income, income)

    return render(request, "month_result.html", {
        "start": start,
        "end": end,
        "offset": month_offset,

        "income": income,
        "costs": costs,
        "expenses": expenses,
        "other_income": other_income,

        "gross_profit": gross_profit,
        "net_profit": net_profit,

        "income_by_category": income_by_category,
        "expenses_list": expenses_list,
        "expenses_by_category": expenses_by_category,
        "other_income_list": other_income_list,
        "other_income_by_category": other_income_by_category,

        "costs_pct": costs_pct,
        "gross_margin_pct": gross_margin_pct,
        "net_margin_pct": net_margin_pct,
        "expenses_pct": expenses_pct,
        "other_income_pct": other_income_pct,
    })


@login_required
def user_profile(request):
    return render(request, "user_profile.html", {
        "user": request.user
    })


@login_required
def export_data(request):
    from datetime import datetime

    models_to_export = [
        "Category", "Tag", "ExpenseCategory", "Product", "ProductImage",
        "Department", "Customer",
        "PurchaseInvoice", "Purchase", "SaleInvoice", "Sale", "Expense",
        "OtherIncomeCategory", "OtherIncome",
    ]
    data = {
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "version": "1.3",
            "model_count": len(models_to_export),
        },
        "data": {}
    }

    for model_name in models_to_export:
        model = apps.get_model("stock", model_name)
        queryset = model.objects.all()
        serialized_json = serializers.serialize("json", queryset)
        serialized_data = json.loads(serialized_json)
        data["data"][model_name] = serialized_data

    response = HttpResponse(json.dumps(data, indent=2, ensure_ascii=False),
                            content_type="application/json")
    response["Content-Disposition"] = 'attachment; filename="mi-stock-backup-{}.json"'.format(
        datetime.now().strftime("%Y%m%d-%H%M%S"))
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
        models_order = [
            "Category", "Tag", "ExpenseCategory", "Product", "ProductImage",
            "Department", "Customer",
            "PurchaseInvoice", "Purchase", "SaleInvoice", "Sale", "Expense",
            "OtherIncomeCategory", "OtherIncome",
        ]
        imported_counts = {}

        for model_name in models_order:
            if model_name not in data.get("data", {}):
                continue
            serialized_list = data["data"][model_name]
            json_str = json.dumps(serialized_list)
            imported = 0
            for obj in serializers.deserialize("json", json_str):
                obj.save()
                imported += 1
            imported_counts[model_name] = imported

        messages.success(request, f"Datos importados exitosamente: {imported_counts}")
        return redirect("home")

    return render(request, "import_form.html")


@login_required
def top_products_view(request, period='mes'):
    """
    Vista para mostrar productos más vendidos.
    Periodos: hoy, semana, mes, total
    """
    today = now().date()
    week_date = today - timedelta(days=7)
    month_start = today.replace(day=1)
    sem_start = today.replace(month=(7 if today.month > 6 else 1), day=1)
    year_start = today.replace(month=1, day=1)

    if period == 'hoy':
        date_filter = {'invoice__date__gte': today}
        title = "Productos Más Vendidos - Hoy"
    elif period == 'semana':
        date_filter = {'invoice__date__gte': week_date}
        title = "Productos Más Vendidos - Última Semana"
    elif period == 'mes':
        date_filter = {'invoice__date__gte': month_start}
        title = "Productos Más Vendidos - Mes Actual"
    elif period == 'semestre':
        date_filter = {'invoice__date__gte': sem_start}
        title = "Productos Más Vendidos - Semestre Actual"
    elif period == 'año':
        date_filter = {'invoice__date__gte': year_start}
        title = "Productos Más Vendidos - Año Actual"
    elif period == 'total':
        date_filter = {}
        title = "Productos Más Vendidos - Total Histórico"
    else:
        raise Http404("Período no válido")

    top_products = (
        Sale.objects.filter(**date_filter)
        .values('product__name', 'product__category__name')
        .annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price'))
        )
        .order_by('-total_revenue')
    )

    total_revenue_all = top_products.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0

    class TopProduct:
        def __init__(self, pk, product_name, category_name,
                     total_sold, total_revenue, percentage):
            self.id = pk
            self.product_name = product_name
            self.category_name = category_name or "Sin categoría"
            self.total_sold = total_sold
            self.total_revenue = total_revenue
            self.percentage = percentage
            self.percentage_display = f"{percentage:.2f}%"

    products_list = []
    for idx, item in enumerate(top_products, start=1):
        percentage = (item['total_revenue'] / total_revenue_all * 100
                      if total_revenue_all > 0 else 0)
        product = TopProduct(
            pk=idx,
            product_name=item['product__name'],
            category_name=item['product__category__name'],
            total_sold=item['total_sold'],
            total_revenue=item['total_revenue'],
            percentage=percentage
        )
        products_list.append(product)

    fields = ["Producto", "Categoría", "Cantidad Vendida",
              "Ingresos Totales", "% por Ingresos"]
    columns = ["product_name", "category_name", "total_sold",
               "total_revenue", "percentage_display"]

    context = {
        'title': title,
        'model': 'product',
        'fields': fields,
        'columns': columns,
        'page_obj': products_list,
        'show_actions': False,
    }

    return render(request, 'list.html', context)


@login_required
def sales_by_department(request, period='mes'):
    """Ventas agrupadas por departamento del cliente."""
    today = now().date()
    month_start = today.replace(day=1)
    sem_start = today.replace(month=(7 if today.month > 6 else 1), day=1)
    year_start = today.replace(month=1, day=1)

    if period == 'mes':
        date_filter = {'invoice__date__gte': month_start}
        title = "Ventas por Departamento - Mes Actual"
    elif period == 'semestre':
        date_filter = {'invoice__date__gte': sem_start}
        title = "Ventas por Departamento - Semestre Actual"
    elif period == 'año':
        date_filter = {'invoice__date__gte': year_start}
        title = "Ventas por Departamento - Año Actual"
    elif period == 'total':
        date_filter = {}
        title = "Ventas por Departamento - Total Histórico"
    else:
        raise Http404("Período no válido")

    rows = (
        Sale.objects.filter(**date_filter, invoice__customer_obj__isnull=False)
        .values("invoice__customer_obj__department__name")
        .annotate(
            total_sold=Sum("quantity"),
            total_revenue=Sum(F("quantity") * F("price")),
        )
        .order_by("-total_revenue")
    )

    total_revenue_all = sum(r["total_revenue"] or 0 for r in rows)

    class DeptRow:
        def __init__(self, idx, department_name, total_sold, total_revenue, percentage):
            self.id = idx
            self.department_name = department_name or "Sin departamento"
            self.total_sold = total_sold
            self.total_revenue = total_revenue
            self.percentage = percentage
            self.percentage_display = f"{percentage:.2f}%"

    items = []
    for idx, item in enumerate(rows, start=1):
        percentage = (
            (item["total_revenue"] / total_revenue_all * 100)
            if total_revenue_all else 0
        )
        items.append(DeptRow(
            idx,
            item["invoice__customer_obj__department__name"],
            item["total_sold"],
            item["total_revenue"],
            percentage,
        ))

    fields = ["Departamento", "Unidades Vendidas", "Ingresos Totales", "% por Ingresos"]
    columns = ["department_name", "total_sold", "total_revenue", "percentage_display"]

    return render(request, "list.html", {
        "title": title,
        "model": "department",
        "fields": fields,
        "columns": columns,
        "page_obj": items,
        "show_actions": False,
    })


@login_required
def sales_by_tag(request, period='mes'):
    """Ventas agrupadas por etiqueta del producto."""
    today = now().date()
    month_start = today.replace(day=1)
    sem_start = today.replace(month=(7 if today.month > 6 else 1), day=1)
    year_start = today.replace(month=1, day=1)

    if period == 'mes':
        date_filter = {'invoice__date__gte': month_start}
        title = "Ventas por Etiqueta - Mes Actual"
    elif period == 'semestre':
        date_filter = {'invoice__date__gte': sem_start}
        title = "Ventas por Etiqueta - Semestre Actual"
    elif period == 'año':
        date_filter = {'invoice__date__gte': year_start}
        title = "Ventas por Etiqueta - Año Actual"
    elif period == 'total':
        date_filter = {}
        title = "Ventas por Etiqueta - Total Histórico"
    else:
        raise Http404("Período no válido")

    rows = (
        Sale.objects.filter(**date_filter, product__tags__isnull=False)
        .values("product__tags__id", "product__tags__name")
        .annotate(
            total_sold=Sum("quantity"),
            total_revenue=Sum(F("quantity") * F("price")),
        )
        .order_by("-total_revenue")
    )

    total_revenue_all = sum(r["total_revenue"] or 0 for r in rows)

    class TagRow:
        def __init__(self, idx, tag_id, tag_name, total_sold, total_revenue, percentage):
            self.id = idx
            self.tag_id = tag_id
            self.tag_name = tag_name or "Sin etiqueta"
            self.total_sold = total_sold
            self.total_revenue = total_revenue
            self.percentage = percentage
            self.percentage_display = f"{percentage:.2f}%"

    items = []
    for idx, item in enumerate(rows, start=1):
        percentage = (
            (item["total_revenue"] / total_revenue_all * 100)
            if total_revenue_all else 0
        )
        items.append(TagRow(
            idx,
            item["product__tags__id"],
            item["product__tags__name"],
            item["total_sold"],
            item["total_revenue"],
            percentage,
        ))

    fields = ["Etiqueta", "Unidades Vendidas", "Ingresos Totales", "% por Ingresos"]
    columns = ["tag_name", "total_sold", "total_revenue", "percentage_display"]

    return render(request, "list.html", {
        "title": title,
        "model": "tag",
        "fields": fields,
        "columns": columns,
        "page_obj": items,
        "show_actions": False,
    })