# Generated by Django 5.0.1 on 2024-04-10 22:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory_management", "0007_stocktransfer_observations"),
    ]

    operations = [
        migrations.AddField(
            model_name="productunit",
            name="quantity",
            field=models.IntegerField(default=1, verbose_name="Quantidade"),
        ),
        migrations.AlterField(
            model_name="productunit",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="inventory_management.product",
                verbose_name="Produto",
            ),
        ),
    ]