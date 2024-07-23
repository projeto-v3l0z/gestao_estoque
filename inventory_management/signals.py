from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import *

@receiver(post_save, sender=Color)
def create_or_update_products_with_color(sender, instance, created, **kwargs):
    if created:
        for product in Product.objects.filter(name__contains="liso", color__isnull=True):
            Product.objects.create(name=f"{product.name.capitalize()} {instance.name}", description=product.description, price=product.price, measure=product.measure, width=product.width, composition=product.composition, image=product.image, code=product.code, ncm=product.ncm, color=instance, pattern=product.pattern, created_by=product.created_by, updated_by=product.updated_by)
    else:
        Product.objects.filter(color=instance).delete()


@receiver(post_save, sender=Pattern)
def create_or_update_products_with_pattern(sender, instance, created, **kwargs):
    if created:
        for product in Product.objects.filter(name__contains="estampado", pattern__isnull=True):
            Product.objects.create(name=f"{product.name.capitalize()} {instance.name}", description=product.description, price=product.price, measure=product.measure, width=product.width, composition=product.composition, image=product.image, code=product.code, ncm=product.ncm, color=product.color, pattern=instance, created_by=product.created_by, updated_by=product.updated_by)
    else:
        Product.objects.filter(pattern=instance).delete()
        

@receiver(post_save, sender=Product)
def update_or_create_related_products(sender, instance, created, **kwargs):
    if created:
        if "liso" in instance.name.lower() and instance.color is None:
            for color in Color.objects.all():
                Product.objects.create(
                    name=f"{instance.name.capitalize()} {color.name}",
                    description=instance.description,
                    price=instance.price,
                    measure=instance.measure,
                    width=instance.width,
                    composition=instance.composition,
                    image=instance.image,
                    code=instance.code,
                    ncm=instance.ncm,
                    color=color,
                    pattern=instance.pattern,
                    created_by=instance.created_by,
                    updated_by=instance.updated_by,
                    slug=slugify(f"{instance.name} {color.name}")
                )
        if "estampado" in instance.name.lower() and instance.pattern is None:
            for pattern in Pattern.objects.all():
                Product.objects.create(
                    name=f"{instance.name.capitalize()} {pattern.name}",
                    description=instance.description,
                    price=instance.price,
                    measure=instance.measure,
                    width=instance.width,
                    composition=instance.composition,
                    image=instance.image,
                    code=instance.code,
                    ncm=instance.ncm,
                    color=instance.color,
                    pattern=pattern,
                    created_by=instance.created_by,
                    updated_by=instance.updated_by,
                    slug=slugify(f"{instance.name} {pattern.name}")
                )
    else:
        if "liso" in instance.name.lower():
            prefix = instance.name
            if instance.color and instance.name.lower().endswith(instance.color.name.lower()):
                prefix = instance.name[:-len(instance.color.name)].strip()
            Product.objects.filter(
                Q(name__icontains=prefix) & ~Q(pk=instance.pk)
            ).update(
                description=instance.description,
                price=instance.price,
                measure=instance.measure,
                width=instance.width,
                composition=instance.composition,
                code=instance.code,
                ncm=instance.ncm,
                updated_by=instance.updated_by
            )
        if "estampado" in instance.name.lower():
            prefix = instance.name
            if instance.pattern and instance.name.lower().endswith(instance.pattern.name.lower()):
                prefix = instance.name[:-len(instance.pattern.name)].strip()
            Product.objects.filter(
                Q(name__icontains=prefix) & ~Q(pk=instance.pk) 
            ).update(
                description=instance.description,
                price=instance.price,
                measure=instance.measure,
                width=instance.width,
                composition=instance.composition,
                code=instance.code,
                ncm=instance.ncm,
                updated_by=instance.updated_by
            )
            
@receiver(post_delete, sender=Product)
def delete_related_products(sender, instance, **kwargs):
    if "liso" in instance.name.lower():
        Product.objects.filter(
            Q(name__icontains=instance.name) & ~Q(pk=instance.pk)
        ).delete()
    elif "estampado" in instance.name.lower():
        Product.objects.filter(
            Q(name__icontains=instance.name) & ~Q(pk=instance.pk) 
        ).delete()


@receiver(pre_save, sender=Product)
def validate_unique_name(sender, instance, **kwargs):
    if not instance.pk:
        if Product.objects.filter(name__iexact=instance.name).exists():
            raise ValidationError("Esse nome já está em uso.")
