# Generated by Django 5.0.1 on 2024-04-11 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_management', '0008_productunit_quantity_alter_productunit_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='media/product_images', verbose_name='Imagem'),
        ),
    ]