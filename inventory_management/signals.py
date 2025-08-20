import re
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from .models import *

# Função auxiliar para resolver o usuário atual
def _resolve_user(base_instance=None):
    """
    Tenta resolver o usuário atual seguindo a hierarquia:
    1. Usuário atual do middleware
    2. Usuário do objeto base (quando existir)
    3. Fallback para usuário com ID=1
    """
    from .middleware import get_current_user
    
    # 1. Tenta pegar o usuário atual do middleware
    current_user = get_current_user()
    if current_user and not isinstance(current_user, AnonymousUser):
        return current_user
    
    # 2. Tenta usar o usuário do objeto base
    if base_instance and hasattr(base_instance, 'created_by') and base_instance.created_by:
        return base_instance.created_by
    
    # 3. Fallback para usuário com ID=1
    try:
        User = get_user_model()
        fallback_user = User.objects.get(id=1)
        return fallback_user
    except User.DoesNotExist:
        # Se não existir usuário com ID=1, tenta pegar o primeiro usuário disponível
        try:
            fallback_user = User.objects.first()
            if fallback_user:
                return fallback_user
        except:
            pass
    
    # 4. Último recurso: retorna None (será tratado pelo signal genérico)
    return None


@receiver(post_save, sender=Color)
def create_or_update_products_with_color(sender, instance, created, **kwargs):
    # if created:
    for product in Product.objects.filter(name__contains="liso", color__isnull=True):
        # Resolve o usuário para os campos created_by e updated_by
        user = _resolve_user(product)
        
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
            created_by=user,
            updated_by=user
        )
    # else:
    #     Product.objects.filter(color=instance).delete()


@receiver(post_save, sender=Pattern)
def create_or_update_products_with_pattern(sender, instance, created, **kwargs):
    # if created:
    for product in Product.objects.filter(name__contains="estampado", pattern__isnull=True):
        # Resolve o usuário para os campos created_by e updated_by
        user = _resolve_user(product)
        
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
            created_by=user,
            updated_by=user
        )
    # else:
    #     Product.objects.filter(pattern=instance).delete()
        

# Imports já estão no topo do arquivo, removendo duplicação

@receiver(post_save, sender=Product)
def update_or_create_related_products(sender, instance, created, **kwargs):
    # Define os dados comuns para variações
    product_data = {
        "description": instance.description,
        "price": instance.price,
        "measure": instance.measure,
        "width": instance.width,
        "composition": instance.composition,
        "image": instance.image,
        "ncm": instance.ncm,
    }

    if created:
        with transaction.atomic():
            if "liso" in instance.name.lower() and instance.color is None:
                for color in Color.objects.all():
                    # Resolve o usuário para os campos created_by e updated_by
                    user = _resolve_user(instance)
                    
                    Product.objects.create(
                        name=f"{instance.name.capitalize()} {color.name}",
                        color=color,
                        slug=slugify(f"{instance.name} {color.name}"),
                        created_by=user,
                        updated_by=user,
                        **product_data,
                    )

            elif "estampado" in instance.name.lower() and instance.pattern is None:
                for pattern in Pattern.objects.all():
                    # Resolve o usuário para os campos created_by e updated_by
                    user = _resolve_user(instance)
                    
                    Product.objects.create(
                        name=f"{instance.name.capitalize()} {pattern.name}",
                        pattern=pattern,
                        slug=slugify(f"{instance.name} {pattern.name}"),
                        created_by=user,
                        updated_by=user,
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
                
                # Resolve o usuário para updated_by
                user = _resolve_user(instance)
                if user:
                    product.updated_by = user
                
                # Desconectar o sinal temporariamente para evitar loop
                from django.db.models import signals
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

# Signal genérico para preencher automaticamente os campos de usuário para todos os modelos
# Funciona como fallback para casos onde os campos não foram preenchidos explicitamente
@receiver(pre_save)
def set_user_fields_for_all_models(sender, instance, **kwargs):
    """
    Signal genérico que preenche automaticamente os campos created_by, updated_by, 
    created_at, updated_at para todos os modelos que os possuem.
    Funciona como fallback para casos onde os campos não foram preenchidos explicitamente.
    """
    # Verifica se o modelo tem os campos necessários
    if not hasattr(instance, 'created_by') or not hasattr(instance, 'updated_by'):
        return
    
    # Verifica se é um modelo do Django (não um proxy ou outro tipo)
    if not hasattr(instance, '_meta') or not hasattr(instance._meta, 'model_name'):
        return
    
    # Só executa se os campos não foram preenchidos explicitamente
    if instance.created_by and instance.updated_by:
        return
    
    from .middleware import get_current_user
    
    current_user = get_current_user()
    
    if not instance.pk:  # Nova instância (criação)
        if hasattr(instance, 'created_at') and not instance.created_at:
            instance.created_at = timezone.now()
        if not instance.created_by and current_user and not isinstance(current_user, AnonymousUser):
            instance.created_by = current_user
    
    # Sempre atualizar updated_at e updated_by (apenas se não foi preenchido)
    if hasattr(instance, 'updated_at'):
        instance.updated_at = timezone.now()
    if not instance.updated_by and current_user and not isinstance(current_user, AnonymousUser):
        instance.updated_by = current_user
