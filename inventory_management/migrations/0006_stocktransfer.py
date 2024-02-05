# Generated by Django 5.0 on 2024-02-05 00:55

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_management', '0005_building_slug_alter_category_slug_alter_product_slug_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockTransfer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transfer_date', models.DateField(verbose_name='Data da Transferência')),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='destination', to='inventory_management.room', verbose_name='Destino')),
                ('origin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='origin', to='inventory_management.room', verbose_name='Origem')),
                ('product_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory_management.productunit', verbose_name='Unidade de Produto')),
            ],
            options={
                'verbose_name': 'Transferência de Estoque',
                'verbose_name_plural': 'Transferências de Estoque',
            },
        ),
    ]
