from django.urls import path, re_path
from django.http import HttpResponseNotFound
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("favicon.ico", lambda request: HttpResponseNotFound()),
    path("top-productos/<str:period>/", views.top_products_view, name="top_products_period"),
    path("top-productos/", views.top_products_view, {"period": "mes"}, name="top_products"),
    re_path(r"^(?P<model_str>category|product|sale|purchase|expense|expensecategory)$",
            views.generic_list_view, name="list"),
    # CRUD genérico para modelos simples (excepto product, que usa su propia vista)
    re_path(r"^(?P<model_str>category|expense|expensecategory)/new$",
            views.generic_form_view, name="new"),
    re_path(r"^(?P<model_str>category|expense|expensecategory)/(?P<pk>\d+)/edit$",
            views.generic_form_view, name="edit"),
    # Producto con marca y fotos
    path("product/new/", views.product_form_view, name="product_new"),
    path("product/<int:pk>/edit/", views.product_form_view, name="product_edit"),
    path("compras/new/", views.purchase_invoice_form_view, name="purchase_invoice_new"),
    path("compras/<int:pk>/edit/", views.purchase_invoice_form_view, name="purchase_invoice_edit"),
    path("ventas/new/", views.sale_invoice_form_view, name="sale_invoice_new"),
    path("ventas/<int:pk>/edit/", views.sale_invoice_form_view, name="sale_invoice_edit"),
    path("resultados/<int:month_offset>/",
         views.month_result, name="month_result"),
    path("resultados/", views.month_result, {"month_offset": 0}),
    path("perfil/", views.user_profile, name="user_profile"),
    path("exportar/", views.export_data, name="export_data"),
    path("importar/", views.import_data, name="import_data"),
]