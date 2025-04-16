from django.urls import path
from .views import *

urlpatterns = [
    path("", product_list, name="product_list"),
    path("products/create/", product_create, name="product_create"),
]
