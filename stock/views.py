from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import (
    Category, ExpenseCategory, Product,
    Purchase, Sale, Expense,
    PurchaseInvoice, SaleInvoice,
    OtherIncomeCategory, OtherIncome,
    Customer,
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


# ===== Listas dedicadas (vistas y templates propios) =====


@login_required
def product_list_view(request):
    """Lista de productos con tabs activos/inactivos y filtro por etiqueta."""
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

    def _serialize(qs):
        rows = []
        for p in qs:
            rows.append([
                p.name,
                p.category.name if p.category else "",
                ", ".join(t.name for t in p.tags.all()),
                str(p.stock),
                str(p.price),
                str(p.average_cost),
                {
                    "detail": reverse("product_detail", args=[p.id]),
                    "edit": reverse("product_edit", args=[p.id]),
                    "toggle": reverse("product_toggle_active", args=[p.id]),
                    "active": p.active,
                    "next": request.get_full_path(),
                },
            ])
        return rows

    context = {
        "title": "Productos",
        "tab": tab,
        "headers_json": json.dumps(
            ["Nombre", "Categoría", "Etiquetas", "Stock", "Precio",
             "Costo Promedio", "Acciones"]
        ),
        "active_count": active_qs.count(),
        "inactive_count": inactive_qs.count(),
        "active_data_json": json.dumps(_serialize(active_qs)),
        "inactive_data_json": json.dumps(_serialize(inactive_qs)),
        "available_tags": list(Tag.objects.all().values("id", "name")),
        "selected_tag": selected_tag,
        "clear_url": request.path + "?tab=" + tab,
    }
    return render(request, "product_list.html", context)


@login_required
def purchase_list_view(request):
    """Lista de facturas de compra con filtro por etiqueta."""
    tag_id = request.GET.get("tag")
    selected_tag = None
    if tag_id and tag_id.isdigit():
        selected_tag = Tag.objects.filter(pk=int(tag_id)).first()
    invoices = PurchaseInvoice.objects.all()
    if selected_tag:
        invoices = invoices.filter(items__product__tags=selected_tag).distinct()

    rows = []
    for inv in invoices:
        rows.append([
            inv.date.strftime("%d/%m/%Y"),
            inv.supplier,
            ", ".join(f"{i.quantity} × {i.product.name}" for i in inv.items.all()),
            str(inv.get_total()),
            {
                "detail": reverse("purchase_invoice_detail", args=[inv.id]),
                "edit": reverse("purchase_invoice_edit", args=[inv.id]),
            },
        ])

    context = {
        "title": "Compras",
        "headers_json": json.dumps(
            ["Fecha", "Proveedor", "Productos", "Total", "Acciones"]
        ),
        "data_json": json.dumps(rows),
        "available_tags": list(Tag.objects.all().values("id", "name")),
        "selected_tag": selected_tag,
        "clear_url": request.path,
    }
    return render(request, "purchase_list.html", context)


@login_required
def sale_list_view(request):
    """Lista de facturas de venta con filtro por etiqueta."""
    tag_id = request.GET.get("tag")
    selected_tag = None
    if tag_id and tag_id.isdigit():
        selected_tag = Tag.objects.filter(pk=int(tag_id)).first()
    invoices = SaleInvoice.objects.select_related("customer_obj").all()
    if selected_tag:
        invoices = invoices.filter(items__product__tags=selected_tag).distinct()

    rows = []
    for inv in invoices:
        rows.append([
            inv.date.strftime("%d/%m/%Y"),
            inv.customer_obj.name,
            ", ".join(f"{i.quantity} × {i.product.name}" for i in inv.items.all()),
            str(inv.get_total()),
            {
                "detail": reverse("sale_invoice_detail", args=[inv.id]),
                "edit": reverse("sale_invoice_edit", args=[inv.id]),
            },
        ])

    context = {
        "title": "Ventas",
        "headers_json": json.dumps(
            ["Fecha", "Cliente", "Productos", "Total", "Acciones"]
        ),
        "data_json": json.dumps(rows),
        "available_tags": list(Tag.objects.all().values("id", "name")),
        "selected_tag": selected_tag,
        "clear_url": request.path,
    }
    return render(request, "sale_list.html", context)


# ===== CRUD dedicado por modelo (vistas y templates propios) =====


# --- Category ---

@login_required
def category_list_view(request):
    rows = [
        [c.name, {"edit": reverse("category_edit", args=[c.id])}]
        for c in Category.objects.all()
    ]
    context = {
        "title": "Categorías",
        "headers_json": json.dumps(["Nombre", "Acciones"]),
        "data_json": json.dumps(rows),
    }
    return render(request, "category_list.html", context)


@login_required
def category_form_view(request, pk=None):
    obj = get_object_or_404(Category, pk=pk) if pk else None
    title = ("Editar " if obj else "Agregar nueva ") + "Categoría"
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("category_list") if pk else redirect("category_new")
    else:
        form = CategoryForm(instance=obj)
    return render(request, "category_form.html", {"title": title, "form": form})


# --- Tag ---

@login_required
def tag_list_view(request):
    rows = [
        [t.name, {"edit": reverse("tag_edit", args=[t.id])}]
        for t in Tag.objects.all()
    ]
    context = {
        "title": "Etiquetas",
        "headers_json": json.dumps(["Nombre", "Acciones"]),
        "data_json": json.dumps(rows),
    }
    return render(request, "tag_list.html", context)


@login_required
def tag_form_view(request, pk=None):
    obj = get_object_or_404(Tag, pk=pk) if pk else None
    title = ("Editar " if obj else "Agregar nueva ") + "Etiqueta"
    if request.method == "POST":
        form = TagForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("tag_list") if pk else redirect("tag_new")
    else:
        form = TagForm(instance=obj)
    return render(request, "tag_form.html", {"title": title, "form": form})


# --- ExpenseCategory ---

@login_required
def expensecategory_list_view(request):
    rows = [
        [ec.name, {"edit": reverse("expensecategory_edit", args=[ec.id])}]
        for ec in ExpenseCategory.objects.all()
    ]
    context = {
        "title": "Categorías de Gastos",
        "headers_json": json.dumps(["Nombre", "Acciones"]),
        "data_json": json.dumps(rows),
    }
    return render(request, "expensecategory_list.html", context)


@login_required
def expensecategory_form_view(request, pk=None):
    obj = get_object_or_404(ExpenseCategory, pk=pk) if pk else None
    title = ("Editar " if obj else "Agregar nueva ") + "Categoría de Gasto"
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("expensecategory_list") if pk else redirect("expensecategory_new")
    else:
        form = ExpenseCategoryForm(instance=obj)
    return render(request, "expensecategory_form.html", {"title": title, "form": form})


# --- OtherIncomeCategory ---

@login_required
def otherincomecategory_list_view(request):
    rows = [
        [oic.name, {"edit": reverse("otherincomecategory_edit", args=[oic.id])}]
        for oic in OtherIncomeCategory.objects.all()
    ]
    context = {
        "title": "Categorías de Otros Ingresos",
        "headers_json": json.dumps(["Nombre", "Acciones"]),
        "data_json": json.dumps(rows),
    }
    return render(request, "otherincomecategory_list.html", context)


@login_required
def otherincomecategory_form_view(request, pk=None):
    obj = get_object_or_404(OtherIncomeCategory, pk=pk) if pk else None
    title = ("Editar " if obj else "Agregar nueva ") + "Categoría de Otro Ingreso"
    if request.method == "POST":
        form = OtherIncomeCategoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("otherincomecategory_list") if pk else redirect("otherincomecategory_new")
    else:
        form = OtherIncomeCategoryForm(instance=obj)
    return render(request, "otherincomecategory_form.html", {"title": title, "form": form})


# --- Customer ---

@login_required
def customer_list_view(request):
    rows = []
    for c in Customer.objects.select_related("department"):
        rows.append([
            c.name,
            c.whatsapp or "",
            c.department.name if c.department else "",
            "Sí" if c.active else "No",
            {"edit": reverse("customer_edit", args=[c.id])},
        ])
    context = {
        "title": "Clientes",
        "headers_json": json.dumps(
            ["Nombre", "WhatsApp", "Departamento", "Activo", "Acciones"]
        ),
        "data_json": json.dumps(rows),
    }
    return render(request, "customer_list.html", context)


@login_required
def customer_form_view(request, pk=None):
    obj = get_object_or_404(Customer, pk=pk) if pk else None
    title = ("Editar " if obj else "Agregar nuevo ") + "Cliente"
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("customer_list") if pk else redirect("customer_new")
    else:
        form = CustomerForm(instance=obj)
    return render(request, "customer_form.html", {"title": title, "form": form})


# --- Expense ---

@login_required
def expense_list_view(request):
    rows = []
    for e in Expense.objects.select_related("category"):
        rows.append([
            e.date.strftime("%d/%m/%Y"),
            e.category.name if e.category else "",
            e.description or "",
            str(e.amount),
            {"edit": reverse("expense_edit", args=[e.id])},
        ])
    context = {
        "title": "Gastos",
        "headers_json": json.dumps(
            ["Fecha", "Categoría", "Descripción", "Monto", "Acciones"]
        ),
        "data_json": json.dumps(rows),
    }
    return render(request, "expense_list.html", context)


@login_required
def expense_form_view(request, pk=None):
    obj = get_object_or_404(Expense, pk=pk) if pk else None
    title = ("Editar " if obj else "Agregar nuevo ") + "Gasto"
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("expense_list") if pk else redirect("expense_new")
    else:
        form = ExpenseForm(instance=obj)
    return render(request, "expense_form.html", {"title": title, "form": form})


# --- OtherIncome ---

@login_required
def otherincome_list_view(request):
    rows = []
    for oi in OtherIncome.objects.select_related("category"):
        rows.append([
            oi.date.strftime("%d/%m/%Y"),
            oi.category.name if oi.category else "",
            oi.description or "",
            str(oi.amount),
            {"edit": reverse("otherincome_edit", args=[oi.id])},
        ])
    context = {
        "title": "Otros Ingresos",
        "headers_json": json.dumps(
            ["Fecha", "Categoría", "Descripción", "Monto", "Acciones"]
        ),
        "data_json": json.dumps(rows),
    }
    return render(request, "otherincome_list.html", context)


@login_required
def otherincome_form_view(request, pk=None):
    obj = get_object_or_404(OtherIncome, pk=pk) if pk else None
    title = ("Editar " if obj else "Agregar nuevo ") + "Otro Ingreso"
    if request.method == "POST":
        form = OtherIncomeForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Se ha guardado correctamente.")
            return redirect("otherincome_list") if pk else redirect("otherincome_new")
    else:
        form = OtherIncomeForm(instance=obj)
    return render(request, "otherincome_form.html", {"title": title, "form": form})


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
        "list_url": reverse("product_list"),
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

    next_url = request.POST.get("next") or reverse("product_list")
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
        "list_url": reverse("purchase_list"),
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
        "list_url": reverse("sale_list"),
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


# Períodos comunes de los reportes
REPORT_PERIODS = [
    ("hoy", "Hoy"),
    ("semana", "Semana"),
    ("mes", "Mes"),
    ("semestre", "Semestre"),
    ("año", "Año"),
    ("total", "Total"),
]


@login_required
def top_products_view(request, period='mes'):
    """Top de productos vendidos en un período."""
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

    total_revenue_all = sum(r["total_revenue"] or 0 for r in top_products)

    rows = []
    for item in top_products:
        revenue = item['total_revenue'] or 0
        percentage = (revenue / total_revenue_all * 100
                      if total_revenue_all > 0 else 0)
        rows.append([
            item['product__name'],
            item['product__category__name'] or "Sin categoría",
            str(item['total_sold']),
            str(revenue),
            f"{percentage:.2f}%",
        ])

    context = {
        'title': title,
        'headers_json': json.dumps(
            ["Producto", "Categoría", "Cantidad Vendida",
             "Ingresos Totales", "% por Ingresos"]
        ),
        'data_json': json.dumps(rows),
        'period': period,
        'periods': REPORT_PERIODS,
    }
    return render(request, 'top_products.html', context)


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

    items = []
    for item in rows:
        total_revenue = item["total_revenue"] or 0
        percentage = (
            (total_revenue / total_revenue_all * 100)
            if total_revenue_all else 0
        )
        items.append([
            item["invoice__customer_obj__department__name"] or "Sin departamento",
            str(item["total_sold"]),
            str(total_revenue),
            f"{percentage:.2f}%",
        ])

    return render(request, "sales_by_department.html", {
        "title": title,
        "headers_json": json.dumps(
            ["Departamento", "Unidades Vendidas", "Ingresos Totales",
             "% por Ingresos"]
        ),
        "data_json": json.dumps(items),
        "period": period,
        "periods": REPORT_PERIODS,
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

    items = []
    for item in rows:
        total_revenue = item["total_revenue"] or 0
        percentage = (
            (total_revenue / total_revenue_all * 100)
            if total_revenue_all else 0
        )
        items.append([
            item["product__tags__name"] or "Sin etiqueta",
            str(item["total_sold"]),
            str(total_revenue),
            f"{percentage:.2f}%",
        ])

    return render(request, "sales_by_tag.html", {
        "title": title,
        "headers_json": json.dumps(
            ["Etiqueta", "Unidades Vendidas", "Ingresos Totales",
             "% por Ingresos"]
        ),
        "data_json": json.dumps(items),
        "period": period,
        "periods": REPORT_PERIODS,
    })