# Generated by Django 5.0.1 on 2024-05-12 04:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_management', '0035_alter_write_off_write_off_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='destinations',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Nome do Local'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Nome do Funcionário'),
        ),
    ]
