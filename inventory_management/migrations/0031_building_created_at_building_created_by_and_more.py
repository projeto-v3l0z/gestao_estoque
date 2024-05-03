# Generated by Django 5.0.1 on 2024-05-03 07:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_management', '0030_alter_write_off_write_off_date'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='building',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='building',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='building_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='building',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='building',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='building_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='clothconsumption',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='clothconsumption',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cloth_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='clothconsumption',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='clothconsumption',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cloth_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='color',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='color',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='color_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='color',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='color',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='color_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='hall',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='hall',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hall_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='hall',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='hall',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hall_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='pattern',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='pattern',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pattern_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='pattern',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='pattern',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pattern_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='product',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='product',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='product',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='productunit',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='productunit',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='productunit_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='productunit',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='productunit',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='productunit_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='room',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='room',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='room_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='room',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='room',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='room_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='shelf',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='shelf',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shelf_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='shelf',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='shelf',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shelf_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stock_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='stocktransfer',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='stock_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
        migrations.AddField(
            model_name='write_off',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Criado em'),
        ),
        migrations.AddField(
            model_name='write_off',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='writeoff_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Criado por'),
        ),
        migrations.AddField(
            model_name='write_off',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Atualizado em'),
        ),
        migrations.AddField(
            model_name='write_off',
            name='updated_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='writeoff_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Atualizado por'),
        ),
    ]
