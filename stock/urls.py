from django.urls import path, re_path
from django.http import HttpResponseNotFound
from . import views
from . import api

urlpatterns = [
    path("", views.home, name="home"),
    # API pública de productos (solo lectura, sin login). Ver docs/api.md
    path("api/products/", api.api_product_list, name="api_product_list"),
    path("api/products/<int:pk>/", api.api_product_detail, name="api_product_detail"),
    path("favicon.ico", lambda request: HttpResponseNotFound()),
    path("top-productos/<str:period>/", views.top_products_view, name="top_products_period"),
    path("top-productos/", views.top_products_view, {"period": "mes"}, name="top_products"),
    re_path(r"^(?P<model_str>category|product|sale|purchase|expense|expensecategory|otherincome|otherincomecategory|customer|tag)$",
            views.generic_list_view, name="list"),
    # CRUD genérico para modelos simples (excepto product, que usa su propia vista)
    re_path(r"^(?P<model_str>category|expense|expensecategory|otherincome|otherincomecategory|customer|tag)/new$",
            views.generic_form_view, name="new"),
    re_path(r"^(?P<model_str>category|expense|expensecategory|otherincome|otherincomecategory|customer|tag)/(?P<pk>\d+)/edit$",
            views.generic_form_view, name="edit"),
    # Producto con marca y fotos
    path("product/new/", views.product_form_view, name="product_new"),
    path("product/<int:pk>/", views.product_detail_view, name="product_detail"),
    path("product/<int:pk>/edit/", views.product_form_view, name="product_edit"),
    path("compras/new/", views.purchase_invoice_form_view, name="purchase_invoice_new"),
    path("compras/<int:pk>/edit/", views.purchase_invoice_form_view, name="purchase_invoice_edit"),
    path("compras/<int:pk>/", views.purchase_invoice_detail_view, name="purchase_invoice_detail"),
    path("ventas/new/", views.sale_invoice_form_view, name="sale_invoice_new"),
    path("ventas/<int:pk>/edit/", views.sale_invoice_form_view, name="sale_invoice_edit"),
    path("ventas/<int:pk>/", views.sale_invoice_detail_view, name="sale_invoice_detail"),
    path("resultados/<int:month_offset>/",
         views.month_result, name="month_result"),
    path("resultados/", views.month_result, {"month_offset": 0}),
    path("reportes/ventas-por-departamento/",
         views.sales_by_department, {"period": "mes"}, name="sales_by_department"),
    path("reportes/ventas-por-departamento/<str:period>/",
         views.sales_by_department, name="sales_by_department_period"),
    path("reportes/ventas-por-etiqueta/",
         views.sales_by_tag, {"period": "mes"}, name="sales_by_tag"),
    path("reportes/ventas-por-etiqueta/<str:period>/",
         views.sales_by_tag, name="sales_by_tag_period"),
    path("perfil/", views.user_profile, name="user_profile"),
    path("exportar/", views.export_data, name="export_data"),
    path("importar/", views.import_data, name="import_data"),
]