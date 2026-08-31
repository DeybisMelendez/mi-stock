import django.db.models.deletion
from django.db import migrations, models


DEPARTMENTS = [
    ("Boaco", "BOA"),
    ("Carazo", "CAR"),
    ("Chinandega", "CHI"),
    ("Chontales", "CHO"),
    ("Estelí", "EST"),
    ("Granada", "GRA"),
    ("Jinotega", "JIN"),
    ("León", "LEO"),
    ("Madriz", "MAD"),
    ("Managua", "MAN"),
    ("Masaya", "MAS"),
    ("Matagalpa", "MAT"),
    ("Nueva Segovia", "NVS"),
    ("Río San Juan", "RSJ"),
    ("Rivas", "RIV"),
    ("RACCN", "RCN"),
    ("RACCS", "RCS"),
]


def seed_departments(apps, schema_editor):
    Department = apps.get_model("stock", "Department")
    for name, code in DEPARTMENTS:
        Department.objects.create(name=name, code=code)


def unseed_departments(apps, schema_editor):
    Department = apps.get_model("stock", "Department")
    codes = [code for _, code in DEPARTMENTS]
    Department.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("stock", "0010_product_active"),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
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
                ("name", models.CharField(max_length=50, unique=True)),
                ("code", models.CharField(max_length=3, unique=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(seed_departments, unseed_departments),
    ]
