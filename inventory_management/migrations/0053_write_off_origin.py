# Generated by Django 5.0.1 on 2024-05-17 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_management', '0052_remove_write_off_origin_shelf_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='write_off',
            name='origin',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Origem'),
        ),
    ]
