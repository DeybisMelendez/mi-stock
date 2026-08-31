import django.db.models.deletion
from django.db import migrations, models


def backfill_customers(apps, schema_editor):
    Customer = apps.get_model("stock", "Customer")
    SaleInvoice = apps.get_model("stock", "SaleInvoice")

    nombres = (
        SaleInvoice.objects
        .exclude(customer__isnull=True)
        .exclude(customer__exact="")
        .exclude(customer__exact="Generic")
        .values_list("customer", flat=True)
        .distinct()
    )

    name_to_id = {}
    for nombre in nombres:
        customer, _ = Customer.objects.get_or_create(name=nombre)
        name_to_id[nombre] = customer.id

    for invoice in SaleInvoice.objects.exclude(customer__isnull=True).exclude(customer__exact=""):
        cid = name_to_id.get(invoice.customer)
        if cid is not None:
            invoice.customer_obj_id = cid
            invoice.save(update_fields=["customer_obj"])


def reverse_backfill(apps, schema_editor):
    SaleInvoice = apps.get_model("stock", "SaleInvoice")
    SaleInvoice.objects.update(customer_obj=None)


class Migration(migrations.Migration):

    dependencies = [
        ("stock", "0011_department_sow_nicaragua"),
    ]

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("whatsapp", models.CharField(blank=True, max_length=20)),
                ("address", models.CharField(blank=True, max_length=300)),
                ("notes", models.TextField(blank=True, null=True)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "department",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="stock.department",
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="saleinvoice",
            name="customer_obj",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="invoices",
                to="stock.customer",
            ),
        ),
        migrations.RunPython(backfill_customers, reverse_backfill),
    ]
