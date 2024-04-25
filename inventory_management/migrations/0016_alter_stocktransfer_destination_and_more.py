# Generated by Django 5.0.1 on 2024-04-24 18:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "inventory_management",
            "0015_remove_hall_shelf_remove_room_hall_hall_room_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="stocktransfer",
            name="destination",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="destination",
                to="inventory_management.shelf",
                verbose_name="Destino",
            ),
        ),
        migrations.AlterField(
            model_name="stocktransfer",
            name="origin",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="origin",
                to="inventory_management.shelf",
                verbose_name="Origem",
            ),
        ),
    ]