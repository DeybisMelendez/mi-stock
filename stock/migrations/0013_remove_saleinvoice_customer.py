import django.db.models.deletion
from django.db import migrations, models


GENERIC_CUSTOMER_NAME = "Cliente Genérico"


def backfill_customer_obj_required(apps, schema_editor):
    Customer = apps.get_model("stock", "Customer")
    SaleInvoice = apps.get_model("stock", "SaleInvoice")

    generic_customer, _ = Customer.objects.get_or_create(
        name=GENERIC_CUSTOMER_NAME,
    )

    invoices = SaleInvoice.objects.filter(customer_obj__isnull=True).exclude(customer__exact="").exclude(customer__exact="Generic").exclude(customer__isnull=True)
    name_to_id = {}
    for invoice in invoices:
        nombre = invoice.customer
        if nombre not in name_to_id:
            customer, _ = Customer.objects.get_or_create(name=nombre)
            name_to_id[nombre] = customer.id
        invoice.customer_obj_id = name_to_id[nombre]
        invoice.save(update_fields=["customer_obj"])

    SaleInvoice.objects.filter(
        customer_obj__isnull=True
    ).update(customer_obj=generic_customer)


def reverse_backfill(apps, schema_editor):
    SaleInvoice = apps.get_model("stock", "SaleInvoice")
    SaleInvoice.objects.filter(customer_obj__name=GENERIC_CUSTOMER_NAME).update(customer_obj=None)


class Migration(migrations.Migration):

    dependencies = [
        ("stock", "0012_customer_saleinvoice_customer_obj"),
    ]

    operations = [
        migrations.RunPython(backfill_customer_obj_required, reverse_backfill),
        migrations.AlterField(
            model_name="saleinvoice",
            name="customer_obj",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="invoices",
                to="stock.customer",
            ),
        ),
        migrations.RemoveField(
            model_name="saleinvoice",
            name="customer",
        ),
    ]