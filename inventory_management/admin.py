from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.urls import path
from django.shortcuts import redirect
from django.utils.safestring import mark_safe

import base64
from io import BytesIO
import qrcode
from django.contrib import admin
from .models import *

admin.site.site_header = 'Gestão de Estoque'
admin.site.site_title = 'Administração'
admin.site.index_title = 'Gestão de Estoque'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'custom_display', 'created_by', 'created_at', 'updated_by', 'updated_at')
    search_fields = ('name',)
    
    def custom_display(self, obj):
        if "liso" in obj.name.lower():
            return obj.color
        elif "estampado" in obj.name.lower():
            return obj.pattern 
        else:
            return "N/A"
    custom_display.short_description = "Liso/Estampado" 
    
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


def download_qr_codes(modeladmin, request, queryset):
    item_ids = ','.join(str(item.id) for item in queryset)
    url = reverse('inventory_management:generate_qr_codes') + f'?selected_items={item_ids}'
    return redirect(url)
    

download_qr_codes.short_description = "Gerar QR Codes"


def write_off_products(modeladmin, request, queryset):
    for product_unit in queryset:
        if not product_unit.write_off:
            product_unit.write_off = True
            product_unit.save()
write_off_products.short_description = "Dar baixa em produtos selecionados"

def write_on_products(modeladmin, request, queryset):
    for product_unit in queryset:
        if product_unit.write_off:
            product_unit.write_off = False
            product_unit.save()
write_on_products.short_description = "Retornar ao estoque os produtos selecionados"

class ClothConsumptionInline(admin.TabularInline):
    model = ClothConsumption
    readonly_fields = ('remainder','weight_length_before')
    extra = 1

class StockTransferInline(admin.TabularInline):
    model = StockTransfer
    readonly_fields = ('origin_storage_type','origin_shelf','destination_storage_type', 'destination_shelf', 'transfer_date', 'observations')
    extra = 0

    
@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = ('id','product', 'code' ,'location','shelf_or_none','weight_length_with_measure', 'write_off' , 'was_written_off' ,'qr_code_generated','purchase_date', "created_by", "created_at", "updated_by", "updated_at")
    search_fields = ('product__name', 'location__name', 'id', 'code')
    list_filter = ('product' ,'purchase_date', 'location', 'write_off', 'was_written_off' ,'qr_code_generated')
    fields = ['product', 'quantity', 'weight_length', 'incoming',]
    actions = [download_qr_codes, write_off_products, write_on_products]
    inlines = [ClothConsumptionInline, StockTransferInline]
    

    class Media:
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
            'admin/product_unit_admin.js',
        )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj:
            last_fieldset_index = len(fieldsets) - 1 
            last_fieldset = list(fieldsets[last_fieldset_index])
            updated_fields = list(last_fieldset[1]['fields']) + ['purchase_date', 'code', 'qr_code_image', 'write_off', 'qr_code_generated']
            last_fieldset[1]['fields'] = updated_fields
            fieldsets[last_fieldset_index] = tuple(last_fieldset)
            
        return fieldsets
    
    def shelf_or_none(self, obj):
        if obj.shelf:
            return obj.shelf
        return "N/A"
    shelf_or_none.short_description = 'Gaveta'

    def weight_length_with_measure(self, obj):
        if obj.product.measure != 'u':
            product_measure = obj.product.get_measure_display()
            return f"{obj.weight_length} {product_measure}"
        else:
            return "Unitário"
    weight_length_with_measure.short_description = 'Metro/Kg'

    def qr_code_image(self, obj):
        if obj:
            absolute_url = f"{obj.get_absolute_url()}"
            qr = qrcode.make(absolute_url)
            qr_io = BytesIO()
            qr.save(qr_io, format='PNG')
            qr_io.seek(0)
            qr_base64 = base64.b64encode(qr_io.getvalue()).decode('utf-8')
            return mark_safe(f'<img src="data:image/png;base64,{qr_base64}" width="250" height="250"/>')
        return "No QR code available"
    qr_code_image.short_description = 'QR Code'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['quantity'].widget = forms.HiddenInput()
            form.base_fields['weight_length'].disabled = True
            form.base_fields['incoming'].disabled = True
        return form
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "location":
            kwargs["queryset"] = StorageType.objects.exclude(name__in=["Baixa", "Conferência"])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('product','location', 'purchase_date','code' ,'qr_code_image', 'building', 'room', 'hall', 'shelf', 'write_off', 'qr_code_generated',)
        return self.readonly_fields

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('customize_qr_codes/', self.customize_qr_codes),
        ]
        return my_urls + urls

    def customize_qr_codes(self, request):
        return download_qr_codes(self, request, None)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_custom_qr_button'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_custom_qr_button'] = True
        return super().add_view(request, form_url, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_custom_qr_button'] = True
        return super().changelist_view(request, extra_context=extra_context)

    def get_inline_instances(self, request, obj=None):
        if obj:
            return [inline(self.model, self.admin_site) for inline in self.inlines]
        else:
            return []
        
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        
        super().save_model(request, obj, form, change)

@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'transfer_date', 'created_by', 'created_at', 'updated_by', 'updated_at')
    search_fields = ('product_unit__product__name', 'origin_building__name', 'origin_hall__name', 'origin_room__name', 'origin_shelf__name', 'destination_building__name', 'destination_hall__name', 'destination_room__name', 'destination_shelf__name', 'product_unit__product__code')
    list_filter = ('transfer_date', 'origin_shelf', 'destination_shelf')
    fields = ['product_unit', 'origin_storage_type','origin_building','origin_hall','origin_room', 'origin_shelf', 'destination_storage_type','destination_building', 'destination_hall', 'destination_room', 'destination_shelf', 'observations']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('product_unit', 'origin_storage_type', 'origin_shelf','destination_storage_type', 'destination_shelf', 'transfer_date')
        return self.readonly_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "destination_storage_type":
            kwargs["queryset"] = StorageType.objects.exclude(name__in=["Baixa", "Conferência"])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    class Media:
        js = ('admin/autocomplete_origin.js',)

    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)



@admin.register(Write_off)
class WriteOffAdmin(admin.ModelAdmin):
    list_display = ('product_unit', 'write_off_date', 'write_off_destination_or_none', 'created_by', 'created_at', 'updated_by', 'updated_at')
    search_fields = ('product_unit__product__name', 'product_unit__location__name')
    list_filter = ('write_off_date',)
    

    class Media:
        js = ('admin/admin_write_off.js',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "storage_type":
            kwargs["queryset"] = StorageType.objects.filter(name = "Baixa")
        if db_field.name == "recomission_storage_type":
            kwargs["queryset"] = StorageType.objects.exclude(name__in=["Baixa", "Conferência"])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def write_off_destination_or_none(self, obj):
        if obj.write_off_destination:
            return obj.write_off_destination
        return "N/A"
    write_off_destination_or_none.short_description = 'Destinatário da baixa'   

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['origin'].widget = forms.HiddenInput() 
        return form

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('product_unit', 'write_off_date')
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'cep', 'street', 'number', 'complement', 'neighborhood', 'city', 'state', 'created_by', 'created_at', 'updated_by', 'updated_at')
    search_fields = ('name', 'cep', 'street', 'number', 'complement', 'neighborhood', 'city', 'state')
    list_filter = ('street', 'neighborhood', 'city')
   
    class Media:
        js = ('admin/autocomplete_address.js',)

    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    pass

@admin.register(Rooms)
class RoomsAdmin(admin.ModelAdmin):
    class Media:
        js = ('admin/building_models.js',)
    pass


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    class Media:
        js = ('admin/building_models.js',)
    pass

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    pass

@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    pass

@admin.register(WriteOffDestinations)
class WriteOffDestinationsAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'updated_by', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StorageType)
class StorageTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'updated_by', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        
@admin.register(WorkSpace)
class WorkSpaceAdmin(admin.ModelAdmin):
    pass

