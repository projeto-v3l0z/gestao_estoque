# Generated by Django 5.0.1 on 2024-07-25 14:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_management', '0074_alter_productunit_weight_length'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='color',
            options={'ordering': ['name'], 'verbose_name': 'Cor', 'verbose_name_plural': 'Cores'},
        ),
        migrations.AlterModelOptions(
            name='pattern',
            options={'ordering': ['name'], 'verbose_name': 'Estampa', 'verbose_name_plural': 'Estampas'},
        ),
    ]
