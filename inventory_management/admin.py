from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.urls import path

from django.shortcuts import redirect
#

from django.contrib import admin
from .models import *

admin.site.site_header = 'Gestão de Estoque'
admin.site.site_title = 'Administração'
admin.site.index_title = 'Gestão de Estoque'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'custom_display')
    search_fields = ('name',)
    list_filter = ('category',)
    
    def custom_display(self, obj):
        if "liso" in obj.name.lower():
            return obj.color
        elif "estampado" in obj.name.lower():
            return obj.pattern 
        else:
            return "N/A"
    custom_display.short_description = "Liso/Estampado" 
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not obj and form.base_fields.get('color'):
            form.base_fields['color'].widget = forms.HiddenInput()
        elif not obj and form.base_fields.get('pattern'):
            form.base_fields['pattern'].widget = forms.HiddenInput()
        return form

def download_qr_codes(modeladmin, request, queryset):
    item_ids = ','.join(str(item.id) for item in queryset)
    url = reverse('inventory_management:generate_qr_codes') + f'?selected_items={item_ids}'
    return redirect(url)
    

download_qr_codes.short_description = "Baixar QR Codes"

@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = ('product', 'location', 'meters' ,'purchase_date')
    search_fields = ('product__name', 'location__name', 'id', 'code')
    list_filter = ('product' ,'purchase_date', 'location')
    actions = [download_qr_codes]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['quantity'].widget = forms.HiddenInput()
        else:
            pass
        return form

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('location',)
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

@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'transfer_date')
    search_fields = ('product_unit__product__name', 'origin__name', 'destination__name')
    list_filter = ('transfer_date', 'origin', 'destination')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('product_unit', 'origin', 'destination', 'transfer_date')
        return self.readonly_fields

    class Media:
        js = ('admin/autocomplete_origin.js',)

class RoomInline(admin.StackedInline):
    model = Room
    
    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            return 0
        return 1 

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'cep', 'street', 'number', 'complement', 'neighborhood', 'city', 'state')
    search_fields = ('name', 'cep', 'street', 'number', 'complement', 'neighborhood', 'city', 'state')
    list_filter = ('street', 'neighborhood', 'city')
    inlines = [
        RoomInline,
    ]
    
    class Media:
        js = ('admin/autocomplete_address.js',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    
    def change_view(self, request, object_id):
        room = self.get_object(request, object_id)
        building_id = room.building.id
        building_change_url = reverse('admin:inventory_management_building_change', args=[building_id])
        return HttpResponseRedirect(building_change_url)
    
    def has_view_permission(self, request):
        return False
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request):
        return False

@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    pass

@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    pass

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    pass

@admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    pass

@admin.register(StockReposition)
class StockRepositionAdmin(admin.ModelAdmin):
    list_display = ('product_unit', 'reposition_date')
    search_fields = ('product__name', 'quantity')
    list_filter = ('reposition_date', 'product_unit')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('product_unit', 'reposition_date')
        return self.readonly_fields
    
@admin.register(StockWriteOff)
class StockWriteOffAdmin(admin.ModelAdmin):
    list_display = ('product_unit', 'write_off_date')
    search_fields = ('product__name', 'quantity')
    list_filter = ('write_off_date', 'product_unit')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('product_unit', 'write_off_date')
        return self.readonly_fields
    