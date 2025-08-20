import re
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db import transaction
from .models import *

@receiver(post_save, sender=Color)
def create_or_update_products_with_color(sender, instance, created, **kwargs):
    # if created:
    for product in Product.objects.filter(name__contains="liso", color__isnull=True):
        # Verificar se o usuário existe e é válido antes de usar
        created_by = None
        updated_by = None
        
        try:
            if product.created_by and hasattr(product.created_by, 'is_active') and product.created_by.is_active:
                created_by = product.created_by
        except:
            created_by = None
            
        try:
            if product.updated_by and hasattr(product.updated_by, 'is_active') and product.updated_by.is_active:
                updated_by = product.updated_by
        except:
            updated_by = None
        
        Product.objects.create(
            name=f"{product.name.capitalize()} {instance.name}", 
            description=product.description, 
            price=product.price, 
            measure=product.measure, 
            width=product.width, 
            composition=product.composition, 
            image=product.image, 
            code1=product.code1, 
            code2=product.code2, 
            ncm=product.ncm, 
            color=instance, 
            pattern=product.pattern, 
            created_by=created_by,  # Pode ser None se usuário não existir
            updated_by=updated_by   # Pode ser None se usuário não existir
        )
    # else:
    #     Product.objects.filter(color=instance).delete()


@receiver(post_save, sender=Pattern)
def create_or_update_products_with_pattern(sender, instance, created, **kwargs):
    # if created:
    for product in Product.objects.filter(name__contains="estampado", pattern__isnull=True):
        # Verificar se o usuário existe e é válido antes de usar
        created_by = None
        updated_by = None
        
        try:
            if product.created_by and hasattr(product.created_by, 'is_active') and product.created_by.is_active:
                created_by = product.created_by
        except:
            created_by = None
            
        try:
            if product.updated_by and hasattr(product.updated_by, 'is_active') and product.updated_by.is_active:
                updated_by = product.updated_by
        except:
            updated_by = None
        
        Product.objects.create(
            name=f"{product.name.capitalize()} {instance.name}", 
            description=product.description, 
            price=product.price, 
            measure=product.measure, 
            width=product.width, 
            composition=product.composition, 
            image=product.image, 
            code1=product.code1, 
            code2=product.code2, 
            ncm=product.ncm, 
            color=product.color, 
            pattern=instance, 
            created_by=created_by,  # Pode ser None se usuário não existir
            updated_by=updated_by   # Pode ser None se usuário não existir
        )
    # else:
    #     Product.objects.filter(pattern=instance).delete()
        

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import signals

@receiver(post_save, sender=Product)
def update_or_create_related_products(sender, instance, created, **kwargs):
    # Define os dados comuns para variações
    # Verificar se o usuário existe e é válido antes de usar
    created_by = None
    updated_by = None
    
    try:
        if instance.created_by and hasattr(instance.created_by, 'is_active') and instance.created_by.is_active:
            created_by = instance.created_by
    except:
        created_by = None
        
    try:
        if instance.updated_by and hasattr(instance.updated_by, 'is_active') and instance.updated_by.is_active:
            updated_by = instance.updated_by
    except:
        updated_by = None
    
    product_data = {
        "description": instance.description,
        "price": instance.price,
        "measure": instance.measure,
        "width": instance.width,
        "composition": instance.composition,
        "image": instance.image,
        "ncm": instance.ncm,
        "created_by": created_by,  # Pode ser None se usuário não existir
        "updated_by": updated_by,  # Pode ser None se usuário não existir
    }

    if created:
        with transaction.atomic():
            if "liso" in instance.name.lower() and instance.color is None:
                for color in Color.objects.all():
                    Product.objects.create(
                        name=f"{instance.name.capitalize()} {color.name}",
                        color=color,
                        slug=slugify(f"{instance.name} {color.name}"),
                        **product_data,
                    )

            elif "estampado" in instance.name.lower() and instance.pattern is None:
                for pattern in Pattern.objects.all():
                    Product.objects.create(
                        name=f"{instance.name.capitalize()} {pattern.name}",
                        pattern=pattern,
                        slug=slugify(f"{instance.name} {pattern.name}"),
                        **product_data,
                    )

    else:
        base_name = re.sub(r'\b(liso|estampado)\b.*$', r'\1', instance.name, flags=re.IGNORECASE).strip()
        print(base_name)
        def update_related_products(queryset):
            for product in queryset:
                # Atualiza os dados do produto relacionado
                for key, value in product_data.items():
                    setattr(product, key, value)
                # Desconectar o sinal temporariamente para evitar loop
                signals.post_save.disconnect(update_or_create_related_products, sender=Product)
                product.save()
                signals.post_save.connect(update_or_create_related_products, sender=Product)
        
        if "liso" in instance.name.lower():
            related_products = Product.objects.filter(name__icontains=base_name)
            print('related_products', related_products)
            update_related_products(related_products)
        
        elif "estampado" in instance.name.lower():
            related_products = Product.objects.filter(name__icontains=base_name)
            print('related_products', related_products)
            update_related_products(related_products)


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
