# Generated by Django 5.0.1 on 2024-05-14 21:42

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inventory_management", "0042_workspace"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="category",
        ),
        migrations.DeleteModel(
            name="Category",
        ),
    ]
