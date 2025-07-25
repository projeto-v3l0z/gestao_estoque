from datetime import datetime
import json
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.http import JsonResponse
from django.views import View
from .models import *
from .models import Product
from django.shortcuts import redirect
from .forms import FilterProductForm, FilterProductUnitForm, ProductUnitForm, QRCodeForm, ProductCreateForm
from django.http import HttpResponse
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.shortcuts import render
from io import BytesIO
from django.utils import timezone
from django.db.models import Sum
import re
from decimal import Decimal
from django.db.models import Max, Sum
from django.core.paginator import Paginator, PageNotAnInteger
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.shortcuts import get_object_or_404
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .forms import UploadExcelForm
import pandas as pd
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from reportlab.lib.utils import simpleSplit
from django.contrib.auth import logout
from django.db.models import Q
from django_select2.views import AutoResponseView


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'

class ProductListView(PermissionRequiredMixin, ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    paginate_by = 10
    permission_required = 'inventory_management.view_product'


    def get_queryset(self):
        queryset = super().get_queryset()
        products = self.request.GET.getlist('name', None)
        
        if products:
            queryset = queryset.filter(id__in=products)
            
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = FilterProductForm(self.request.GET or None)
        return context


class ProductDetailView(PermissionRequiredMixin, DetailView):
    model = Product
    template_name = 'product_detail.html'
    permission_required = 'inventory_management.view_product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        write_off = self.request.GET.get('write_off')
        location_id = self.request.GET.get('location')
        prd_code = self.request.GET.get('prd_code')  #lembraar
        building_id = self.request.GET.get('building')
        room_id = self.request.GET.get('room')
        hall_id = self.request.GET.get('hall')
        shelf_id = self.request.GET.get('shelf')
        search = self.request.GET.get('search')

        product_units = product.productunit_set.all()

        if prd_code:  # Aplicar filtro por código do produto
            product_units = product_units.filter(code__icontains=prd_code)

        if search:
           product_units = product_units.filter(code__contains=search.lower())

        if location_id:
            product_units = product_units.filter(location__id=location_id)
        if building_id:
            product_units = product_units.filter(building__id=building_id)
        if room_id:
            product_units = product_units.filter(room__id=room_id)
        if hall_id:
            product_units = product_units.filter(hall__id=hall_id)
        if shelf_id:
            product_units = product_units.filter(shelf__id=shelf_id)

        paginator = Paginator(product_units, 8)
        page = self.request.GET.get('page')
        try:
            product_units_page = paginator.page(page)
        except PageNotAnInteger:
            product_units_page = paginator.page(1)

        total_weight_length = product_units.aggregate(total_weight_length=Sum('weight_length'))['total_weight_length']
        context['total_weight_length'] = total_weight_length if total_weight_length else 0
        context['product_units'] = product_units_page
        context['page_obj'] = product_units_page

        # Passando os dados de filtro
        context['locations'] = StorageType.objects.exclude(name__in=["Baixa"])
        context['buildings'] = Building.objects.all()
        context['rooms'] = Rooms.objects.all()
        context['halls'] = Hall.objects.all()
        context['shelves'] = Shelf.objects.all()

        return context

class ProductUnitDetailView(DetailView):
    model = ProductUnit
    template_name = 'product_unit_detail.html'
    # permission_required = 'inventory_management.view_productunit'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['storage_types'] = StorageType.objects.exclude(name__in=["Baixa"])
        context['buildings'] = Building.objects.all()
        context['rooms'] = Rooms.objects.all()
        context['halls'] = Hall.objects.all()
        context['shelves'] = Shelf.objects.exclude(pk=self.get_object().location.id)
        context['consumptions'] = ClothConsumption.objects.filter(product_unit=self.get_object())
        context['write_offs'] = Write_off.objects.filter(product_unit=self.get_object())
        context['write_off_destinations'] = WriteOffDestinations.objects.all()

        return context

    def post(self, request, *args, **kwargs):
        product_unit = self.get_object()

        if 'write_off' in request.POST:
            return self.write_off(request, product_unit)

        if request.POST.get('back_to_stock') == 'True':
            return self.back_to_stock(request, product_unit)

        if request.POST.get('transfer_stock') == 'True':
            return self.stock_transfer(request, product_unit)

        # --- NOVO: Buscar produto pelo QR code (product_id) ---
        if request.POST.get('product_id') and not request.POST.get('divisoes'):
            product_id = request.POST.get('product_id')
            product_unit = get_object_or_404(ProductUnit, code=product_id.upper())
            produto = {
                'nome': product_unit.product.name,
                'codigo': product_unit.code,
                'metragem': float(product_unit.weight_length) if hasattr(product_unit, 'weight_length') else None,
            }
            return JsonResponse({'success': True, 'produto': produto})

        # --- NOVO: Dividir produto em novas unidades ---
        if request.POST.get('codigo') and request.POST.get('divisoes'):
            codigo = request.POST.get('codigo')
            divisoes = request.POST.get('divisoes')
            try:
                divisoes = json.loads(divisoes)
            except Exception as e:
                return JsonResponse({'success': False, 'error': 'Divisões inválidas.'}, status=400)
            product_unit = get_object_or_404(ProductUnit, code=codigo.upper())
            metragem_disponivel = float(product_unit.weight_length)
            soma_divisoes = sum([float(x) for x in divisoes])
            if soma_divisoes > metragem_disponivel:
                return JsonResponse({'success': False, 'error': 'A soma das divisões excede a metragem disponível.'}, status=400)
            # Marcar original como dividido e criar novas unidades
            product_unit.is_divided = True
            product_unit.save()
            novas_unidades = []
            for metragem in divisoes:
                nova = ProductUnit.objects.create(
                    product=product_unit.product,
                    weight_length=metragem,
                    location=product_unit.location,
                    building=product_unit.building,
                    room=product_unit.room,
                    hall=product_unit.hall,
                    shelf=product_unit.shelf,
                    created_by=request.user,
                    updated_by=request.user,
                    is_divided=False,
                    write_off=product_unit.write_off,
                )
                novas_unidades.append(nova.code)
            # Atualiza metragem da original
            product_unit.weight_length = metragem_disponivel - soma_divisoes
            product_unit.save()
            return JsonResponse({'success': True, 'novas_unidades': novas_unidades, 'reload': True})

        return redirect(product_unit.get_absolute_url())

    def write_off(self, request, product_unit):
        # Salvar a localização original antes da baixa
        original_location = product_unit.shelf if product_unit.shelf else product_unit.location
        
        # Marcar como baixado
        product_unit.write_off = True
        
        # Alterar a localização para "Baixa"
        baixa_storage_type = StorageType.objects.get_or_create(name="Baixa")[0]
        product_unit.location = baixa_storage_type
        
        # Limpar informações de localização física
        product_unit.building = None
        product_unit.hall = None
        product_unit.room = None
        product_unit.shelf = None
        
        write_off_destination_id = request.POST.get('write_off_destination')
        write_off_destination = WriteOffDestinations.objects.get(pk=write_off_destination_id)

        Write_off.objects.create(
            product_unit=product_unit,
            origin=original_location,  # Usar a localização original
            storage_type=baixa_storage_type,
            write_off_date=timezone.now(),
            observations="Baixa de produto",
            write_off_destination=write_off_destination,
            created_by=request.user,
        )

        product_unit.save()
        return redirect(product_unit.get_absolute_url())

    def back_to_stock(self, request, product_unit):
        product_unit.write_off = False
        last_write_off = Write_off.objects.filter(product_unit=product_unit).aggregate(last_write_off_date=Max('write_off_date'))
        last_write_off_date = last_write_off.get('last_write_off_date')

        if last_write_off_date:
            last_write_off = Write_off.objects.filter(product_unit=product_unit, write_off_date=last_write_off_date).first()
            write_off_destination = last_write_off.write_off_destination if last_write_off.write_off_destination else None
        else:
            write_off_destination = None

        location_id = request.POST.get('location')
        location = StorageType.objects.get(pk=location_id)
        building_id = request.POST.get('building')
        room_id = request.POST.get('room')
        hall_id = request.POST.get('hall')
        shelf_id = request.POST.get('shelf')
        storage_type = StorageType.objects.get_or_create(name="Baixa")[0]

        product_unit.location_id = location_id
        room = Rooms.objects.get(pk=room_id) if room_id else None
        building = Building.objects.get(pk=building_id) if building_id else None
        hall = Hall.objects.get(pk=hall_id) if hall_id else None
        shelf = Shelf.objects.get(pk=shelf_id) if shelf_id else None


        if location.is_store == True:
            storage_type = StorageType.objects.get_or_create(name="Baixa")[0]

            Write_off.objects.create(
                product_unit=product_unit,
                origin=storage_type,
                recomission_storage_type=location,
                recomission_building=building,
                recomission_room=room,
                recomission_hall=hall,
                recomission_shelf=shelf,
                write_off_date=timezone.now(),
                observations="Retorno ao estoque",
                storage_type=None,
                write_off_destination=None,
                created_by = request.user,
            )
            if room_id:
                product_unit.room_id = room_id
            else:
                product_unit.room_id = None
            if hall_id:
                product_unit.hall_id = hall_id
            else:
                product_unit.hall_id = None
            if shelf_id:
                product_unit.shelf_id = shelf_id
            else:
                product_unit.shelf_id = None
        else:
            Write_off.objects.create(
            product_unit=product_unit,
            origin=storage_type,
            recomission_storage_type=location,
            write_off_date=timezone.now(),
            observations="Retorno ao estoque",
            storage_type =None,
            write_off_destination=None,
            created_by = request.user,
        )



        consumption = request.POST.get('remainder')
        if consumption:
            consumption_decimal = Decimal(consumption)

            if consumption_decimal > product_unit.weight_length:
                return JsonResponse({'remainder': "O consumo não pode ser maior que o peso/tamanho antes da subtração."}, status=400)

            if consumption_decimal < 0:
                return JsonResponse({'remainder': "O peso/tamanho depois da subtração não pode ser negativo."}, status=400)

            ClothConsumption.objects.create(
                product_unit=product_unit,
                weight_length_before=product_unit.weight_length,
                remainder=consumption_decimal
            )

        product_unit.save()
        return redirect(product_unit.get_absolute_url())

    def stock_transfer(self, request, product_unit):
        destination_id = request.POST.get('location')
        building_id = request.POST.get('building')
        room_id = request.POST.get('room')
        hall_id = request.POST.get('hall')
        shelf_id = request.POST.get('shelf')
        observations = request.POST.get('observations')

        origin = product_unit.location
        destination = StorageType.objects.get(pk=destination_id)

        if destination.is_store == True:
            if building_id:
                building = Building.objects.get(pk=building_id)
            else:
                building = None
            if room_id:
                room = Rooms.objects.get(pk=room_id)
            else:
                room = None
            if hall_id:
                hall = Hall.objects.get(pk=hall_id)
            else:
                hall = None
            if shelf_id:
                shelf = Shelf.objects.get(pk=shelf_id)
            else:
                shelf = None
        else:
            building = None
            room = None
            hall = None
            shelf = None

        StockTransfer.objects.create(
                product_unit=product_unit,
                origin_storage_type=origin,
                origin_building=product_unit.building,
                origin_hall=product_unit.hall,
                origin_room=product_unit.room,
                origin_shelf=product_unit.shelf,
                destination_storage_type=destination,
                destination_shelf=shelf,
                destination_building=building,
                destination_room=room,
                destination_hall=hall,
                transfer_date=timezone.now(),
                observations=observations,
                created_by=request.user,
        )

        product_unit.location = destination

        if destination.is_store == True:
            product_unit.building_id = building_id
            if hall_id:
                product_unit.hall_id = hall_id
            else:
                product_unit.hall_id = None
            if room_id:
                product_unit.room_id = room_id
            else:
                product_unit.room_id = None
            if shelf_id:
                product_unit.shelf_id = shelf_id
            else:
                product_unit.shelf_id = None
        else:
            product_unit.building_id = None
            product_unit.room_id = None
            product_unit.hall_id = None
            product_unit.shelf_id = None

        product_unit.save()
        return redirect(product_unit.get_absolute_url())


class ProductUnitCreateView(PermissionRequiredMixin, CreateView):
    model = ProductUnit
    template_name = 'product_unit/form.html'   
    form_class = ProductUnitForm
    permission_required = 'inventory_management.add_productunit'
    success_url = reverse_lazy('inventory_management:product_unit_list')

class ProductCreateView(PermissionRequiredMixin, CreateView):
    model = Product
    template_name = 'product_create.html'
    form_class =ProductCreateForm
    permission_required = 'inventory_management.add_product_create'
    success_url = reverse_lazy('inventory_management:product_list')  

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        return super().form_valid(form)  

class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductCreateForm
    template_name = 'product_edit.html'

    def get_object(self, queryset=None):
        product_id = self.kwargs.get('product_id')
        return get_object_or_404(Product, id=product_id)

    def form_valid(self, form):
        # Salvando o produto com os novos dados
        product = form.save(commit=False)
        product.updated_by = self.request.user  # Atualiza o usuário que fez a alteração
        product.save()

        # Redireciona para a página de detalhes do produto após a edição
        return redirect('inventory_management:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.get_object()  # Adiciona o produto ao contexto
        return context


class ScanQRView(TemplateView):
    template_name = 'scan_qr.html'


class AboutView(TemplateView):
    template_name = 'about.html'


class AdressesView(PermissionRequiredMixin, ListView):
    model = Building
    template_name = 'adresses.html'
    context_object_name = 'adresses'
    permission_required = 'inventory_management.view_building'


class AddressDetailView(PermissionRequiredMixin, DetailView):
    model = Building
    template_name = 'address.html'
    permission_required = 'inventory_management.view_building'


class GetProductLocationShelfView(View):
    def get(self, request, *args, **kwargs):
        product_unit_id = kwargs.get('product_unit_id')
        try:
            product_unit = ProductUnit.objects.get(id=product_unit_id)
            return JsonResponse({'location': product_unit.location_id, 'building': product_unit.building_id, 'room': product_unit.room_id, 'hall': product_unit.hall_id, 'shelf': product_unit.shelf_id})
        except ProductUnit.DoesNotExist:
            return JsonResponse({}, status=404)


def wrap_text(text, max_width, canvas, font_name, font_size):
    canvas.setFont(font_name, font_size)
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if canvas.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def calculate_items_per_page(page_width, page_height, qr_size, columns):
    available_width = page_width - 100
    available_height = page_height - 100

    max_columns = columns
    max_rows = available_height // (qr_size + 40)  # Ajuste para acomodar o texto extra
    items_per_page = max_rows * max_columns

    return items_per_page

def generate_product_unit_qr_codes(request):
    host = request.get_host()
    if request.method == 'POST':
        selected_items = request.POST.getlist('selected_items')
        size_preset = request.POST.get('size_preset')

        if selected_items and size_preset:
            selected_item_ids = selected_items
            queryset = ProductUnit.objects.filter(id__in=selected_item_ids)

            qr_codes = []
            for item in queryset:
                data = f"http://{host}{item.get_absolute_url()}"
                qr = qrcode.make(data, box_size=get_qr_size(size_preset))
                qr_codes.append((qr, item))
                item.mark_qr_code_generated()

            local_now = timezone.localtime(timezone.now())
            timestamp = local_now.strftime("%d-%m-%Y_%H%M%S")

            unique_products = set(product_unit.product.name for product_unit in queryset)
            products_str = '_'.join(unique_products)
            filename = f"qr_codes_{products_str}_{timestamp}.pdf"

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)

            x_offset = 50
            top_margin = 200
            qr_size = get_qr_size(size_preset)
            page_width, page_height = letter
            if size_preset == 'pequeno':
                columns = 4
            elif size_preset == 'medio':
                columns = 3
            elif size_preset == 'grande':
                columns = 2
                top_margin = 300

            items_per_page = calculate_items_per_page(page_width, page_height, qr_size, columns)

            pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))

            for idx, (qr, item) in enumerate(qr_codes):
                row = idx // columns
                col = idx % columns

                if idx > 0 and idx % items_per_page == 0:
                    c.showPage()

                # Ajustar a posição inicial do QR Code e do texto com base na margem superior
                y_coordinate = page_height - top_margin - (row % (items_per_page // columns)) * (qr_size + 80)
                x_coordinate = 50 + x_offset + col * (qr_size + 20)

                # Nome do produto (acima do QR Code)
                product_name = item.product.name.upper()
                max_width = qr_size
                wrapped_text = wrap_text(product_name, max_width, c, "VeraBd", 9)  # Função para quebrar o texto
                total_text_height = len(wrapped_text) * 11 
                text_start_y = y_coordinate + qr_size + total_text_height + 1  # Começar pelo topo do texto

                for line in wrapped_text:
                    text_width = c.stringWidth(line, "VeraBd", 9)
                    line_x = x_coordinate + (qr_size - text_width) / 2
                    text_start_y -= 10  # Subtrair o espaçamento por linha
                    c.drawString(line_x, text_start_y, line)

                # Desenhar o QR Code
                c.drawInlineImage(qr, x_coordinate, y_coordinate, width=qr_size, height=qr_size)

                # Código da unidade do produto (abaixo do QR Code)
                product_code_metrag = f"{item.code} - {item.weight_length}"
                text_width = c.stringWidth(product_code_metrag, "VeraBd", 9)
                code_x = x_coordinate + (qr_size - text_width) / 2
                c.drawString(code_x, y_coordinate - 5, product_code_metrag)

                # Código do produto (abaixo do QR Code)
                product_code1 = item.product.code1
                product_code2 = item.product.code2
                if product_code1:
                    product_code = f"Código 1: {product_code1}"
                    text_width = c.stringWidth(product_code, "VeraBd", 9)
                    code_x = x_coordinate + (qr_size - text_width) / 2
                    c.drawString(code_x, y_coordinate - 15, product_code)
                if product_code2:
                    product_code = f"Código 2: {product_code2}"
                    text_width = c.stringWidth(product_code, "VeraBd", 9)
                    code_x = x_coordinate + (qr_size - text_width) / 2
                    c.drawString(code_x, y_coordinate - 25, product_code)

            c.showPage()
            c.save()
            pdf_data = buffer.getvalue()
            buffer.close()
            response.write(pdf_data)

            return response
        else:
            messages.error(request, "Selecione pelo menos um item e um tamanho de QR Code.")
            return redirect('inventory_management:product_unit_list')
    else:
        messages.error(request, "Método não permitido.")
        return redirect('inventory_management:product_unit_list')


def generate_qr_codes(request):
    host = request.get_host()
    if request.method == 'POST':
        form = QRCodeForm(request.POST)
        if form.is_valid():
            selected_items = request.GET.get('selected_items')
            size_preset = form.cleaned_data['size_preset']

            if selected_items and size_preset:
                selected_item_ids = selected_items.split(',')
                queryset = ProductUnit.objects.filter(id__in=selected_item_ids)

                qr_codes = []
                for item in queryset:
                    data = f"http://{host}{item.get_absolute_url()}"
                    qr = qrcode.make(data, box_size=get_qr_size(size_preset))
                    qr_codes.append((qr, item))
                    item.mark_qr_code_generated()

                local_now = timezone.localtime(timezone.now())
                timestamp = local_now.strftime("%d-%m-%Y_%H%M%S")

                unique_products = set(product_unit.product.name for product_unit in queryset)
                products_str = '_'.join(unique_products)
                filename = f"qr_codes_{products_str}_{timestamp}.pdf"

                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)

                x_offset = 50
                top_margin = 200
                qr_size = get_qr_size(size_preset)
                page_width, page_height = letter
                if size_preset == 'pequeno':
                    columns = 4
                elif size_preset == 'medio':
                    columns = 3
                elif size_preset == 'grande':
                    columns = 2
                    top_margin = 300

                items_per_page = calculate_items_per_page(page_width, page_height, qr_size, columns)

                pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))
                

              

                for idx, (qr, item) in enumerate(qr_codes):
                    row = idx // columns
                    col = idx % columns

                    if idx > 0 and idx % items_per_page == 0:
                        c.showPage()

                    # Ajustar a posição inicial do QR Code e do texto com base na margem superior
                    y_coordinate = page_height - top_margin - (row % (items_per_page // columns)) * (qr_size + 80)
                    x_coordinate = 50 + x_offset + col * (qr_size + 20)

                    # Nome do produto (acima do QR Code)
                    product_name = item.product.name.upper()
                    max_width = qr_size
                    wrapped_text = wrap_text(product_name, max_width, c, "VeraBd", 9)  # Função para quebrar o texto
                    total_text_height = len(wrapped_text) * 11 
                    text_start_y = y_coordinate + qr_size + total_text_height + 1  # Começar pelo topo do texto

                    for line in wrapped_text:
                        text_width = c.stringWidth(line, "VeraBd", 9)
                        line_x = x_coordinate + (qr_size - text_width) / 2
                        text_start_y -= 10  # Subtrair o espaçamento por linha
                        c.drawString(line_x, text_start_y, line)

                    # Desenhar o QR Code
                    c.drawInlineImage(qr, x_coordinate, y_coordinate, width=qr_size, height=qr_size)

                    # Código do produto (abaixo do QR Code)
                    product_code1 = item.product.code1
                    product_code2 = item.product.code2
                    if product_code1:
                        product_code = f"Código 1: {product_code1}"
                        text_width = c.stringWidth(product_code, "VeraBd", 9)
                        code_x = x_coordinate + (qr_size - text_width) / 2
                        c.drawString(code_x, y_coordinate - 15, product_code)
                    if product_code2:
                        product_code = f"Código 2: {product_code2}"
                        text_width = c.stringWidth(product_code, "VeraBd", 9)
                        code_x = x_coordinate + (qr_size - text_width) / 2
                        c.drawString(code_x, y_coordinate - 25, product_code)

                c.showPage()
                c.save()
                pdf_data = buffer.getvalue()
                buffer.close()
                response.write(pdf_data)

                return response
    else:
        form = QRCodeForm()
    return render(request, 'admin/inventory_management/productunit/generate_qr_codes.html', {'form': form})


def get_qr_size(size_preset):
    if size_preset == 'pequeno':
        return 100
    elif size_preset == 'medio':
        return 150
    elif size_preset == 'grande':
        return 200


@method_decorator(login_required, name='dispatch')
class WorkSpaceWriteOffView(PermissionRequiredMixin ,ListView):
    template_name = 'workspace_write_off.html'
    model = WorkSpace
    permission_required = 'inventory_management.view_workspace'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_transfer'] = self.request.user.has_perm('inventory_management.add_stocktransfer')
        context['can_write_off'] = self.request.user.has_perm('inventory_management.add_write_off')
        context['write_off_destinations'] = WriteOffDestinations.objects.all()
        context['storage_types'] = StorageType.objects.filter(name__icontains="depósito")
        context['shelves'] = Shelf.objects.all()
        context['buildings'] = Building.objects.all()
        context['rooms'] = Rooms.objects.all()
        context['halls'] = Hall.objects.all()
        context['product_count'] = WorkSpace.objects.filter(user=self.request.user).count()
        return context

    def post(self, request, *args, **kwargs):
        try:
            print("POST data:", request.POST)  # Debug: Print the POST data

            if 'clean' in request.POST:
                print("Cleaning workspace")
                WorkSpace.objects.filter(user=request.user).delete()
                return JsonResponse({'success': 'Produtos removidos com sucesso', 'reload': True}, status=200)

            product_id = request.POST.get('product_id')
            remove = request.POST.get('remove')
            write_off_destination_id = request.POST.get('write_off_destination')

            if write_off_destination_id:
                print("Processing write off")
                write_off_destination = get_object_or_404(WriteOffDestinations, pk=write_off_destination_id)
                baixa_storage_type = StorageType.objects.get_or_create(name="Baixa")[0]
                
                for product in WorkSpace.objects.filter(user=request.user):
                    product_unit = product.product
                    
                    # Salvar localização original
                    origin = product_unit.shelf if product_unit.shelf else product_unit.location
                    
                    # Marcar como baixado e alterar localização
                    product_unit.write_off = True
                    product_unit.location = baixa_storage_type
                    product_unit.building = None
                    product_unit.hall = None
                    product_unit.room = None
                    product_unit.shelf = None
                    product_unit.updated_by = request.user
                    product_unit.save()

                    Write_off.objects.create(
                        product_unit=product_unit,
                        origin=origin,  # Localização original
                        storage_type=baixa_storage_type,
                        write_off_date=timezone.now(),
                        observations="Baixa de produto",
                        write_off_destination=write_off_destination,
                        created_by=request.user,
                    )

                WorkSpace.objects.filter(user=request.user).delete()
                return JsonResponse({'success': 'Produtos baixados com sucesso', 'reload': True}, status=200)

            if remove:
                print("Removing product from workspace")
                workspace_item = get_object_or_404(WorkSpace, user=request.user, product__code=remove)
                workspace_item.delete()
                return JsonResponse({'success': 'Produto removido da área de trabalho', 'reload': True}, status=200)

            if product_id:
                product = get_object_or_404(ProductUnit, code=product_id.upper())
                if WorkSpace.objects.filter(user=request.user, product=product).exists():
                    return JsonResponse({'error': 'Produto já está na sua área de trabalho', 'reload': True}, status=400)
                if product.write_off is False:
                    return JsonResponse({'error': 'Esse produto não está baixado', 'reload': True}, status=400)
                if product.is_divided:
                    return JsonResponse({'error': 'Esse produto está dividido, não pode ser adicionado à área de trabalho', 'reload': True}, status=400)

                WorkSpace.objects.create(user=request.user, product=product)
                return JsonResponse({'success': 'Produto adicionado à área de trabalho', 'reload': True}, status=200)

            if request.POST.get('transfer') is not None:
                location_id = request.POST.get('location')
                if not location_id or location_id == "None":
                    return JsonResponse({'error': 'ID de localização inválido'}, status=400)

                destination = get_object_or_404(StorageType, id=location_id)

                building_id = request.POST.get('building')
                building = Building.objects.filter(pk=building_id).first() if building_id else None

                room_id = request.POST.get('room')
                room = Rooms.objects.filter(pk=room_id).first() if room_id else None

                hall_id = request.POST.get('hall')
                hall = Hall.objects.filter(pk=hall_id).first() if hall_id else None

                shelf_id = request.POST.get('shelf')
                shelf = Shelf.objects.filter(pk=shelf_id).first() if shelf_id else None

                observations = request.POST.get('observations', '')

                for product in WorkSpace.objects.filter(user=request.user):
                    product_unit = product.product

                    StockTransfer.objects.create(
                        product_unit=product_unit,
                        origin_storage_type=product_unit.location,
                        origin_building=product_unit.building,
                        origin_hall=product_unit.hall,
                        origin_room=product_unit.room,
                        origin_shelf=product_unit.shelf,
                        destination_storage_type=destination,
                        destination_shelf=shelf,
                        destination_building=building,
                        destination_room=room,
                        destination_hall=hall,
                        transfer_date=timezone.now(),
                        observations=observations,
                        created_by=request.user,
                    )

                    product_unit.location = destination

                    if destination.is_store:
                        product_unit.building_id = building
                        product_unit.room_id = room
                        product_unit.hall_id = hall
                        product_unit.shelf_id = shelf
                    else:
                        product_unit.building_id = None
                        product_unit.room_id = None
                        product_unit.hall_id = None
                        product_unit.shelf_id = None

                    product_unit.save()

                WorkSpace.objects.filter(user=request.user).delete()
                return JsonResponse({'success': 'Produtos transferidos com sucesso', 'transfer': True, 'reload': True}, status=200)
            else:
                print("Transfer button not pressed")

        except Exception as e:
            print("Exception occurred:", str(e))  # Debug: Print the exception
            return JsonResponse({'error': str(e)}, status=400)

        print("Invalid action")  # Debug: Indicate invalid action
        return JsonResponse({'error': 'Ação inválida'}, status=400)
    
@method_decorator(login_required, name='dispatch')
class WorkSpaceDividedView(PermissionRequiredMixin, TemplateView):
    template_name = 'workspace_divided.html'
    permission_required = 'inventory_management.view_workspace'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)
    
    def post(self, request, *args, **kwargs):
        quantidades = request.POST.getlist('quantidade[]')
        metragem_original = float(request.POST.get('metragem_original', 0))
        prd = request.POST.get('prd')
        
        try:
            soma = sum([float(q) for q in quantidades if q.strip()])
            
            product_unit = get_object_or_404(ProductUnit, code__icontains=prd)

            if product_unit.is_divided:
                messages.error(request, "Essa unidade de produto já está dividida.")
                return self.get(request, *args, **kwargs)
            
            if product_unit.weight_length < soma:
                messages.error(request, "A soma das unidades não pode ser maior que a metragem original.")
                return self.get(request, *args, **kwargs)
            
            if product_unit.weight_length <= 0:
                messages.error(request, "A metragem original deve ser maior que zero.")
                return self.get(request, *args, **kwargs)
            
            # a soma tem que ser igual a metragem original
            if soma != metragem_original:
                messages.error(request, "A soma das quantidades deve ser igual à metragem original.")
                return self.get(request, *args, **kwargs)
            
            for quantidade in quantidades:
                if quantidade.strip():
                    quantidade_float = float(quantidade)
                    if quantidade_float <= 0:
                        messages.error(request, "As quantidades devem ser maiores que zero.")
                        return self.get(request, *args, **kwargs)
                    
                    if quantidade_float > product_unit.weight_length:
                        messages.error(request, "A quantidade não pode ser maior que a metragem original.")
                        return self.get(request, *args, **kwargs)
                    
                    nova_unidade = ProductUnit.objects.create(
                        product=product_unit.product,
                        weight_length=quantidade_float,
                        location=product_unit.location,
                        building=product_unit.building,
                        room=product_unit.room,
                        hall=product_unit.hall,
                        shelf=product_unit.shelf,
                        write_off=product_unit.write_off,
                        source_unit=product_unit,
                        created_by=request.user,
                    )
                    nova_unidade.save()

            product_unit.is_divided = True
            product_unit.save()
            messages.success(request, "Unidade de produto dividida com sucesso.")
            return redirect('inventory_management:workspace_divided')
        except ValueError as e:
            messages.error(request, f"Erro ao processar as quantidades: {str(e)}")
            return self.get(request, *args, **kwargs)
    
def get_product_unit_info(request, product_unit_id):
    try:
        product_unit = ProductUnit.objects.exclude(is_divided=True).get(code__icontains=product_unit_id)
        data = {
            'code': product_unit.code,
            'name': product_unit.product.name,
            'weight_length': str(product_unit.weight_length),
            'location': product_unit.location.name if product_unit.location else '',
            'building': product_unit.building.name if product_unit.building else '',
            'room': product_unit.room.name if product_unit.room else '',
            'hall': product_unit.hall.name if product_unit.hall else '',
            'shelf': product_unit.shelf.name if product_unit.shelf else '',
        }
        return JsonResponse(data, status=200)
    except ProductUnit.DoesNotExist:
        return JsonResponse({'error': 'Unidade de produto não encontrada'}, status=404)

@method_decorator(login_required, name='dispatch')
class WorkSpaceView(PermissionRequiredMixin ,ListView):
    template_name = 'workspace.html'
    model = WorkSpace
    permission_required = 'inventory_management.view_workspace'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_transfer'] = self.request.user.has_perm('inventory_management.add_stocktransfer')
        context['can_write_off'] = self.request.user.has_perm('inventory_management.add_write_off')
        context['write_off_destinations'] = WriteOffDestinations.objects.all()
        context['storage_types'] = StorageType.objects.exclude(name__in=["Baixa", "Conferência"])
        context['shelves'] = Shelf.objects.all()
        context['buildings'] = Building.objects.all()
        context['rooms'] = Rooms.objects.all()
        context['halls'] = Hall.objects.all()
        context['product_count'] = WorkSpace.objects.filter(user=self.request.user).count()
        return context

    def post(self, request, *args, **kwargs):
        try:
            print("POST data:", request.POST)  # Debug: Print the POST data

            if 'clean' in request.POST:
                print("Cleaning workspace")
                WorkSpace.objects.filter(user=request.user).delete()
                return JsonResponse({'success': 'Produtos removidos com sucesso', 'reload': True}, status=200)

            product_id = request.POST.get('product_id')
            remove = request.POST.get('remove')
            write_off_destination_id = request.POST.get('write_off_destination')

            if write_off_destination_id:
                print("Processing write off")
                write_off_destination = get_object_or_404(WriteOffDestinations, pk=write_off_destination_id)
                baixa_storage_type = StorageType.objects.get_or_create(name="Baixa")[0]
                
                for product in WorkSpace.objects.filter(user=request.user):
                    product_unit = product.product
                    
                    # Salvar localização original
                    origin = product_unit.shelf if product_unit.shelf else product_unit.location
                    
                    # Marcar como baixado e alterar localização
                    product_unit.write_off = True
                    product_unit.location = baixa_storage_type
                    product_unit.building = None
                    product_unit.hall = None
                    product_unit.room = None
                    product_unit.shelf = None
                    product_unit.updated_by = request.user
                    product_unit.save()

                    Write_off.objects.create(
                        product_unit=product_unit,
                        origin=origin,  # Localização original
                        storage_type=baixa_storage_type,
                        write_off_date=timezone.now(),
                        observations="Baixa de produto",
                        write_off_destination=write_off_destination,
                        created_by=request.user,
                    )

                WorkSpace.objects.filter(user=request.user).delete()
                return JsonResponse({'success': 'Produtos baixados com sucesso', 'reload': True}, status=200)

            if remove:
                print("Removing product from workspace")
                workspace_item = get_object_or_404(WorkSpace, user=request.user, product__code=remove)
                workspace_item.delete()
                return JsonResponse({'success': 'Produto removido da área de trabalho', 'reload': True}, status=200)

            if product_id:
                product = get_object_or_404(ProductUnit, code=product_id.upper())
                if WorkSpace.objects.filter(user=request.user, product=product).exists():
                    return JsonResponse({'error': 'Produto já está na sua área de trabalho', 'reload': True}, status=400)
                if product.write_off:
                    return JsonResponse({'error': 'Esse produto está baixado', 'reload': True}, status=400)
                if product.is_divided:
                    return JsonResponse({'error': 'Esse produto está dividido, não pode ser adicionado à área de trabalho', 'reload': True}, status=400)

                WorkSpace.objects.create(user=request.user, product=product)
                return JsonResponse({'success': 'Produto adicionado à área de trabalho', 'reload': True}, status=200)

            if request.POST.get('transfer') is not None:
                location_id = request.POST.get('location')
                if not location_id or location_id == "None":
                    return JsonResponse({'error': 'ID de localização inválido'}, status=400)

                destination = get_object_or_404(StorageType, id=location_id)

                building_id = request.POST.get('building')
                building = Building.objects.filter(pk=building_id).first() if building_id else None

                room_id = request.POST.get('room')
                room = Rooms.objects.filter(pk=room_id).first() if room_id else None

                hall_id = request.POST.get('hall')
                hall = Hall.objects.filter(pk=hall_id).first() if hall_id else None

                shelf_id = request.POST.get('shelf')
                shelf = Shelf.objects.filter(pk=shelf_id).first() if shelf_id else None

                observations = request.POST.get('observations', '')

                for product in WorkSpace.objects.filter(user=request.user):
                    product_unit = product.product

                    StockTransfer.objects.create(
                        product_unit=product_unit,
                        origin_storage_type=product_unit.location,
                        origin_building=product_unit.building,
                        origin_hall=product_unit.hall,
                        origin_room=product_unit.room,
                        origin_shelf=product_unit.shelf,
                        destination_storage_type=destination,
                        destination_shelf=shelf,
                        destination_building=building,
                        destination_room=room,
                        destination_hall=hall,
                        transfer_date=timezone.now(),
                        observations=observations,
                        created_by=request.user,
                    )

                    product_unit.location = destination

                    if destination.is_store:
                        product_unit.building_id = building
                        product_unit.room_id = room
                        product_unit.hall_id = hall
                        product_unit.shelf_id = shelf
                    else:
                        product_unit.building_id = None
                        product_unit.room_id = None
                        product_unit.hall_id = None
                        product_unit.shelf_id = None

                    product_unit.updated_by = request.user

                    product_unit.save()

                WorkSpace.objects.filter(user=request.user).delete()
                return JsonResponse({'success': 'Produtos transferidos com sucesso', 'transfer': True, 'reload': True}, status=200)
            else:
                print("Transfer button not pressed")

        except Exception as e:
            print("Exception occurred:", str(e))  # Debug: Print the exception
            return JsonResponse({'error': str(e)}, status=400)

        print("Invalid action")  # Debug: Indicate invalid action
        return JsonResponse({'error': 'Ação inválida'}, status=400)


def delete_workspace(request, code):
    code = code.upper()
    WorkSpace.objects.filter(user=request.user, product__code=code).delete()
    return HttpResponseRedirect(reverse('inventory_management:workspace'))

def delete_workspace_write_off(request, code):
    code = code.upper()
    WorkSpace.objects.filter(user=request.user, product__code=code).delete()
    return HttpResponseRedirect(reverse('inventory_management:workspace_write_off'))


def get_building_properties(request):
    building_id = request.GET.get('building_id')
    building = Building.objects.get(id=building_id)
    properties = {
        'has_hall': building.has_hall,
        'has_room': building.has_room,
        'has_shelf': building.has_shelf
    }
    return JsonResponse(properties)


def get_halls(request):
    building_id = request.GET.get('building_id')
    halls = Hall.objects.filter(building_id=building_id)
    data = [{'id': hall.id, 'name': hall.name} for hall in halls]
    return JsonResponse(data, safe=False)


def get_rooms(request):
    building_id = request.GET.get('building_id')
    hall_id = request.GET.get('hall_id')
    if hall_id:
        rooms = Rooms.objects.filter(hall_id=hall_id)
    else:
        rooms = Rooms.objects.filter(building_id=building_id, hall__isnull=True)
    data = [{'id': room.id, 'name': room.name} for room in rooms]
    return JsonResponse(data, safe=False)


def get_shelves(request):
    building_id = request.GET.get('building_id')
    hall_id = request.GET.get('hall_id')
    room_id = request.GET.get('room_id')
    if room_id:
        shelves = Shelf.objects.filter(room_id=room_id)
    elif hall_id:
        shelves = Shelf.objects.filter(hall_id=hall_id)
    else:
        shelves = Shelf.objects.filter(building_id=building_id)
    data = [{'id': shelf.id, 'name': shelf.name} for shelf in shelves]
    return JsonResponse(data, safe=False)


def get_write_off_status(request, product_unit_id):
    product_unit = get_object_or_404(ProductUnit, id=product_unit_id)
    return JsonResponse({'write_off': product_unit.write_off})


def get_storage_type_is_store(request):
    storage_type_id = request.GET.get('id')
    if storage_type_id is not None:
        try:
            storage_type = StorageType.objects.get(id=storage_type_id)
            return JsonResponse({'is_store': storage_type.is_store})
        except StorageType.DoesNotExist:
            return JsonResponse({'error': 'StorageType not found'}, status=404)
    return JsonResponse({'error': 'No ID provided'}, status=400)


def check_admin(user):
    return user.is_superuser


@method_decorator(user_passes_test(check_admin), name='dispatch')
class DashboardView(TemplateView):
    template_name = 'admin/dashboard.html'

    
@method_decorator(user_passes_test(check_admin), name='dispatch')
class UploadExcelView(View):
    template_name = 'upload_excel.html'

    MEASURE_MAPPING = {
        'KG': 'kg',
        'MT': 'm',
        'CM': 'cm',
        'G': 'g',
        'UND': 'u',
        'UN': 'u'
    }

    def get(self, request):
        form = UploadExcelForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UploadExcelForm(request.POST, request.FILES)

        if form.is_valid():
            arquivo = request.FILES['file']
            try:
                df = pd.read_excel(arquivo, sheet_name=None)
                sheets = df.keys()

                products_added, products_updated = self.process_products(df.get('PRODUTOS'))

                locations_added, locations_updated = self.process_locations(df.get('LOCALIZAÇÕES'))

                self.show_success_message(products_added, products_updated, locations_added, locations_updated)
            except Exception as e:
                self.show_error_message(request, f'Erro ao processar arquivo: {e}')
                return redirect('inventory_management:load_data')

            return redirect('inventory_management:load_data')

        self.show_error_message(request, 'Ocorreu um erro com o upload do arquivo. Por favor, verifique o formato e tente novamente.')
        return render(request, self.template_name, {'form': form})

    def process_products(self, products_df):
        added = 0
        updated = 0

        if products_df is not None:
            products_df.columns = ['nome', 'preco', 'ncm', 'unidade']
            for _, row in products_df.iterrows():
                created = self.create_or_update_product(row)
                if created:
                    added += 1
                else:
                    updated += 1

        return added, updated

    def create_or_update_product(self, row):
        mapped_unit = self.MEASURE_MAPPING.get(row['unit'].upper(), 'u')
        name_lower = row['name'].strip().lower()
        product, created = Product.objects.update_or_create(
            name=name_lower,
            defaults={
                'ncm': row['ncm'],
                'price': row['preco'],
                'measure': mapped_unit,
                'updated_by': self.request.user,
                'updated_at': timezone.now()
            }
        )
        if created:
            product.created_by = self.request.user
            product.created_at = timezone.now()
        else:
            product.updated_by = self.request.user
            product.updated_at = timezone.now()
        product.save()
        return created

    def process_locations(self, locations_df):
        added = {"building": 0, "hall": 0, "room": 0, "shelf": 0}
        updated = {"building": 0, "hall": 0, "room": 0, "shelf": 0}

        if locations_df is not None:
            locations_df.columns = ['depositos', 'corredores', 'salas', 'gavetas']
            for _, row in locations_df.iterrows():
                added, updated = self.create_or_update_location(row, added, updated)

        return added, updated

    def create_or_update_location(self, row, added, updated):

        building, created = Building.objects.update_or_create(
            name=row['depositos'],
            defaults={'updated_at': timezone.now()}
        )
        added, updated = self.update_counts(added, updated, 'building', created)

        hall_name = row['corredores'].strip().upper()
        if hall_name != "SEM":
            hall, created = Hall.objects.update_or_create(
                name=row['corredores'],
                building=building,
                defaults={'updated_at': timezone.now()}
            )
            added, updated = self.update_counts(added, updated, 'hall', created)
        else:
            hall = None

        room_name = row['salas'].strip().upper()
        if room_name != "SEM":
            room, created = Rooms.objects.update_or_create(
                name=row['salas'],
                hall=hall,
                building=building,
                defaults={'updated_at': timezone.now()}
            )
            added, updated = self.update_counts(added, updated, 'room', created)
        else:
            room = None

        shelves = self.process_shelf_range(row['gavetas'], room, hall, building)
        for shelf in shelves:
            shelf_obj, created = Shelf.objects.update_or_create(
                name=str(shelf),
                room=room,
                hall=hall,
                building=building,
                defaults={'updated_at': timezone.now()}
            )
            added, updated = self.update_counts(added, updated, 'shelf', created)

        return added, updated

    def process_shelf_range(self, shelf_range, room, hall, building):
        shelves = []
        match = re.match(r"DE (\d+) A (\d+)", shelf_range.strip())
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            shelves.extend(range(start, end + 1))
        elif shelf_range.strip().upper() == "SEM":
            return shelves
        return shelves

    def update_counts(self, added, updated, entity, created):
        if created:
            added[entity] += 1
        else:
            updated[entity] += 1
        return added, updated

    def show_success_message(self, products_added, products_updated, locations_added, locations_updated):
        message = (
            f'{products_added} produtos adicionados, {products_updated} produtos atualizados. '
            f'Dados de Localização: '
            f'{locations_added["building"]} Depósitos adicionados, {locations_updated["building"]} atualizados; '
            f'{locations_added["hall"]} Corredores adicionados, {locations_updated["hall"]} atualizados; '
            f'{locations_added["room"]} Salas adicionadas, {locations_updated["room"]} atualizados; '
            f'{locations_added["shelf"]} Gavetas adicionadas, {locations_updated["shelf"]} atualizados.'
        )
        messages.success(self.request, message)

    def show_error_message(self, request, message):
        messages.error(request, message)
        
        
def logout_view(request):
    logout(request)
    return redirect('admin:login')

class ProductUnitListView(LoginRequiredMixin, ListView):
    model = ProductUnit
    template_name = 'product_unit_list.html'
    context_object_name = 'product_units'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        code_search = self.request.GET.get('code', '').strip()  # Filtro por código
        products = self.request.GET.getlist('product', '')  # Filtro por nome do produto
        location_id = self.request.GET.get('location')
        creation_date = self.request.GET.get('created_at') 
        filter_baixado = self.request.GET.get('filter_baixado')  # Novo filtro

        if code_search:
            queryset = queryset.filter(code__icontains=code_search)

        if products:
            queryset = queryset.filter(product__id__in=products)

        if location_id:
            queryset = queryset.filter(location__id=location_id).filter(write_off=False)

        if creation_date:
            date = datetime.strptime(creation_date, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date=date).filter(write_off=False)

        # Filtro por baixado/não baixado
        if filter_baixado == "sim":
            queryset = queryset.filter(write_off=True)
        elif filter_baixado == "nao":
            queryset = queryset.filter(write_off=False)

        return queryset.order_by('-code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = FilterProductUnitForm(self.request.GET or None)
        context['locations'] = StorageType.objects.exclude(name__in=["Baixa"])
        return context

class ProductAutoComplete(View):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("term", "").strip()
        produtos = Product.objects.filter(name__icontains=term)[:10]  # Busca limitada a 10 resultados
        results = [{"id": produto.id, "text": produto.name} for produto in produtos]
        return JsonResponse({"results": results})
    
def recomission_product_units(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.POST.get("recomission", "[]"))
            if not data:
                return JsonResponse({"success": False, "error": "Nenhum item recebido"}, status=400)

            for item in data:
                product_unit_id = item.get("id")
                quantity = float(item.get("quantity", 0))
                storage_type_id = item.get("storageType", "")
                building_id = item.get("building")
                hall_id = item.get("hall") 
                room_id = item.get("room")
                shelf_id = item.get("shelf")

                product_unit = get_object_or_404(ProductUnit, id=product_unit_id)
                storage_type = get_object_or_404(StorageType, id=storage_type_id)
                baixa_storage_type = StorageType.objects.get_or_create(name="Baixa")[0]
                
               
                product_unit.write_off = False
                product_unit.location = storage_type
                
                
                if storage_type.is_store:
                    product_unit.building_id = building_id if building_id else None
                    product_unit.hall_id = hall_id if hall_id else None
                    product_unit.room_id = room_id if room_id else None
                    product_unit.shelf_id = shelf_id if shelf_id else None
                else:
                    product_unit.building = None
                    product_unit.hall = None
                    product_unit.room = None
                    product_unit.shelf = None
                
                product_unit.updated_by = request.user
                product_unit.save()

                
                building = Building.objects.filter(pk=building_id).first() if building_id else None
                hall = Hall.objects.filter(pk=hall_id).first() if hall_id else None
                room = Rooms.objects.filter(pk=room_id).first() if room_id else None
                shelf = Shelf.objects.filter(pk=shelf_id).first() if shelf_id else None

                
                Write_off.objects.create(
                    product_unit=product_unit,
                    origin=baixa_storage_type,  
                    recomission_storage_type=storage_type,  
                    recomission_building=building,
                    recomission_hall=hall,
                    recomission_room=room,
                    recomission_shelf=shelf,
                    write_off_date=timezone.now(),
                    observations="Recomissionamento de produto",
                    storage_type=None,
                    write_off_destination=None,
                    created_by=request.user,
                )

               
                if quantity > 0:
                    ClothConsumption.objects.create(
                        product_unit=product_unit,
                        remainder=quantity
                    )

            WorkSpace.objects.filter(user=request.user).delete()
            return JsonResponse({"success": True, "reload": True})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Erro ao decodificar JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Método não permitido"}, status=405)