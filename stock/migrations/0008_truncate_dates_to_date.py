from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("stock", "0007_expensecategory_product_brand_alter_expense_date_and_more"),
    ]

    operations = [
        # Truncar la parte horaria de los valores datetime que quedaron
        # almacenados al convertir date de DateTimeField a DateField (0007).
        migrations.RunSQL(
            sql=[
                "UPDATE stock_expense SET date = substr(date, 1, 10) "
                "WHERE date LIKE '% %';",
                "UPDATE stock_purchaseinvoice SET date = substr(date, 1, 10) "
                "WHERE date LIKE '% %';",
                "UPDATE stock_saleinvoice SET date = substr(date, 1, 10) "
                "WHERE date LIKE '% %';",
            ],
            reverse_sql=[],
        ),
    ]