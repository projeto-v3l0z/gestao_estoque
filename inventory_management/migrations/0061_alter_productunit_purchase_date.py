# Generated by Django 5.0.1 on 2024-06-13 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_management', '0060_alter_product_options_productunit_was_written_off_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productunit',
            name='purchase_date',
            field=models.DateField(auto_now_add=True, verbose_name='Data de Entrada'),
        ),
    ]
