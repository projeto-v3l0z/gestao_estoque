# Generated by Django 5.0.1 on 2024-04-26 22:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory_management", "0018_productunit_color_productunit_pattern_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="productunit",
            name="code",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Código"
            ),
        ),
    ]
