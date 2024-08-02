from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_storage_type(sender, **kwargs):
    from .models import StorageType
    StorageType.objects.get_or_create(name='Depósito')
    StorageType.objects.get_or_create(name='Loja', is_store=True)
    StorageType.objects.get_or_create(name='Conferência')
    StorageType.objects.get_or_create(name='Baixa')

class InventoryManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory_management'
    verbose_name = 'Gestão de Estoque'

    def ready(self):
        import inventory_management.signals
        post_migrate.connect(create_storage_type, sender=self)