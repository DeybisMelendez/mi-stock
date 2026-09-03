# API pública de productos (solo lectura).
#
# Endpoints:
#   GET /api/products/       → lista de productos activos
#   GET /api/products/<pk>/  → detalle de un producto
#
# "Activo" = active=True (incluye productos con stock=0).
#
# Importante: NUNCA exponer `average_cost` ni `stock` (cantidad). El
# payload se construye con una whitelist explícita de campos para que
# sea imposible filtrarlos por accidente. Se expone un booleano
# derivado `in_stock` que indica si hay existencias, sin revelar la
# cantidad. Ver docs/api.md.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .models import Product


def _product_payload(product, request):
    # Whitelist explícita: si se añade un campo público, se añade aquí.
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": str(product.price),
        "in_stock": product.stock > 0,
        "category": {
            "id": product.category_id,
            "name": product.category.name,
        },
        "tags": [tag.name for tag in product.tags.all()],
        "images": [
            request.build_absolute_uri(image.image.url)
            for image in product.images.all()
            if image.image
        ],
    }


def _active_products():
    return (
        Product.objects
        .filter(active=True)
        .select_related("category")
        .prefetch_related("images", "tags")
    )


@csrf_exempt
@require_GET
def api_product_list(request):
    products = _active_products()
    return JsonResponse(
        {
            "count": products.count(),
            "results": [
                _product_payload(product, request)
                for product in products
            ],
        }
    )


@csrf_exempt
@require_GET
def api_product_detail(request, pk):
    try:
        product = _active_products().get(pk=pk)
    except Product.DoesNotExist:
        return JsonResponse(
            {"error": "Producto no encontrado."}, status=404,
        )
    return JsonResponse(_product_payload(product, request))
