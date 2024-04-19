import os
import tempfile
import zipfile
from django.db.models.query import QuerySet
import qrcode
from django import forms
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.text import slugify
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# from requests import request

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
    list_display = ('name', 'category', 'quantity')
    search_fields = ('name',)
    list_filter = ('category',)
    
def generate_qr_codes_to_pdf(queryset, file_path, request):
    c = canvas.Canvas(file_path, pagesize=letter)

    page_width, page_height = letter
    host = request.get_host()

    for product_unit in queryset:
        # Construir a URL absoluta do item
        absolute_url = f"http://{host}{product_unit.get_absolute_url()}"
        
        # Gerar QR code para a URL
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(absolute_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Salvar a imagem do QR code em um arquivo temporário
        qr_img_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        qr_img.save(qr_img_temp_file)

        # Determinar a posição central do QR code na página
        qr_width, qr_height = qr_img.size
        x_coordinate = (page_width - qr_width) / 2
        y_coordinate = (page_height - qr_height) / 2
        
        # Adicionar o QR code ao PDF
        c.drawImage(qr_img_temp_file.name, x_coordinate, y_coordinate, width=qr_width, height=qr_height)
        
        # Fechar e excluir o arquivo temporário
        qr_img_temp_file.close()

        # Adicionar uma nova página para o próximo QR code
        c.showPage()

    c.save()

def download_qr_codes(modeladmin, request, queryset):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    generate_qr_codes_to_pdf(queryset, temp_file.name, request)

    with open(temp_file.name, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="qr_codes.pdf"'

    temp_file.close()

    return response

download_qr_codes.short_description = "Baixar QR Codes"

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

@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = ('product', 'location', 'purchase_date', 'write_off')
    search_fields = ('product__name', 'location__name')
    list_filter = ('product' ,'purchase_date', 'location', 'write_off')
    actions = [download_qr_codes, write_off_products, write_on_products]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['quantity'].widget = forms.HiddenInput()
        return form

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('location',)
        return self.readonly_fields


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


