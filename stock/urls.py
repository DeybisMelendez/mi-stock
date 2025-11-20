from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("<str:model_str>", views.generic_list_view, name="list"),
    path("<str:model_str>/new", views.generic_form_view, name="new"),
    path("<str:model_str>/<int:pk>/edit", views.generic_form_view, name="edit"),
]
"""
    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("purchases/", views.purchase_list, name="purchase_list"),
    path("purchases/new/", views.purchase_create, name="purchase_create"),
    path("purchases/<int:pk>/edit/", views.purchase_edit, name="purchase_edit"),
    path("sales/", views.sale_list, name="sale_list"),
    path("sales/new/", views.sale_create, name="sale_create"),
    path("sales/<int:pk>/edit/", views.sale_edit, name="sale_edit"),
    """
