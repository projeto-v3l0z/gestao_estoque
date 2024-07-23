from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views import View
from .models import *
from django.shortcuts import redirect
from datetime import date
from .forms import QRCodeForm
from django.http import HttpResponse
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.shortcuts import render
from io import BytesIO
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum
from django.db.models import F, ExpressionWrapper, DecimalField
import io
import base64
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models import Max, Sum
from django.core.paginator import Paginator, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.db.models.functions import TruncMonth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from .forms import UploadExcelForm
import openpyxl
import pandas as pd


class IndexView(TemplateView):
    template_name = 'index.html'
    

class ProductListView(ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__startswith=search)
        return queryset.order_by('name')
    


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_detail.html'
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        write_off = self.request.GET.get('write_off')
        product_units = product.productunit_set.all() 
        search = self.request.GET.get('search')
        
        if search:
            product_units = product_units.filter(id__contains=search)
        
        if write_off == 'baixados':
            product_units = product_units.filter(write_off=True)
        elif write_off == 'todos':
            pass 
        else:
            product_units = product_units.filter(write_off=False)
        
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
        
        return context

class ProductUnitDetailView(DetailView):
    model = ProductUnit
    template_name = 'product_unit_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['storage_types'] = StorageType.objects.exclude(name="Baixa")
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
        
        return redirect(product_unit.get_absolute_url())
    
    def write_off(self, request, product_unit):
        product_unit.write_off = True
        write_off_destination_id = request.POST.get('write_off_destination')
        write_off_destination = WriteOffDestinations.objects.get(pk=write_off_destination_id)
        origin = product_unit.shelf if product_unit.shelf else product_unit.location

        Write_off.objects.create(
            product_unit=product_unit,
            origin=origin,
            storage_type=StorageType.objects.get_or_create(name="Baixa")[0],
            write_off_date=timezone.now(),
            observations="Baixa de produto",
            write_off_destination=write_off_destination
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


        if location.name == "Depósito":
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
        
        if destination.name == "Depósito":
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
        
        if destination.name == "Depósito":
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

    
class ScanQRView(TemplateView):
    template_name = 'scan_qr.html'


class AboutView(TemplateView):
    template_name = 'about.html'


class AdressesView(ListView):
    model = Building
    template_name = 'adresses.html'
    context_object_name = 'adresses'


class AddressDetailView(DetailView):
    model = Building
    template_name = 'address.html'


class GetProductLocationShelfView(View):
    def get(self, request, *args, **kwargs):
        product_unit_id = kwargs.get('product_unit_id')
        try:
            product_unit = ProductUnit.objects.get(id=product_unit_id)
            return JsonResponse({'location': product_unit.location_id, 'building': product_unit.building_id, 'room': product_unit.room_id, 'hall': product_unit.hall_id, 'shelf': product_unit.shelf_id})
        except ProductUnit.DoesNotExist:
            return JsonResponse({}, status=404)
    
def calculate_items_per_page(page_width, page_height, qr_size, columns):
    available_width = page_width - 100 
    available_height = page_height - 100  

    max_columns = columns
    max_rows = available_height // (qr_size + 20)
    items_per_page = max_rows * max_columns

    return items_per_page


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
                qr_size = get_qr_size(size_preset) 
                page_width, page_height = letter
                if size_preset == 'pequeno':
                    columns = 4
                elif size_preset == 'medio':
                    columns = 3
                elif size_preset == 'grande':
                    columns = 2

                items_per_page = calculate_items_per_page(page_width, page_height, qr_size, columns)

                pdfmetrics.registerFont(TTFont('VeraBd', 'VeraBd.ttf'))

                for idx, (qr, item) in enumerate(qr_codes):
                    row = idx // columns  
                    col = idx % columns  
                    page_idx = idx // items_per_page 

                    if size_preset == 'pequeno':
                        y_coordinate = page_height - 200 - (row % (items_per_page // columns)) * (qr_size + 20)
                        x_coordinate = 27 + x_offset + col * (qr_size + 20)
                        text_x_coordinate = x_coordinate - 10
                        text_y_coordinate = y_coordinate + qr_size + 2 
                        text_x_coordinate2 = x_coordinate + 37.5
                        text_y_coordinate2 = y_coordinate - qr_size + 100
                        c.setFont("VeraBd", 6 )
                    elif size_preset == 'medio':
                        y_coordinate = page_height - 200 - (row % (items_per_page // columns)) * (qr_size + 20)
                        x_coordinate = 13 + x_offset + col * (qr_size + 20)
                        text_x_coordinate = x_coordinate
                        text_y_coordinate = y_coordinate + qr_size + 2
                        text_x_coordinate2 = x_coordinate + 58.5
                        text_y_coordinate2 = y_coordinate - qr_size + 155  
                        c.setFont("VeraBd", 8.5 )
                    elif size_preset == 'grande':
                        y_coordinate = page_height - 250 - (row % (items_per_page // columns)) * (qr_size + 20)
                        x_coordinate = 50 + x_offset + col * (qr_size + 20)
                        text_x_coordinate = x_coordinate - 5
                        text_y_coordinate = y_coordinate + qr_size + 2
                        text_x_coordinate2 = x_coordinate + 79.5
                        text_y_coordinate2 = y_coordinate - qr_size + 210
                        c.setFont("VeraBd", 11 )  

                    if idx > 0 and idx % items_per_page == 0:
                        c.showPage()

                    c.drawString(text_x_coordinate, text_y_coordinate, item.product.name)    
                    c.drawInlineImage(qr, x_coordinate, y_coordinate, width=qr_size, height=qr_size)
                    c.drawString(text_x_coordinate2, text_y_coordinate2, item.code)

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
class WorkSpaceView(ListView):
    template_name = 'workspace.html'
    model = WorkSpace

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['write_off_destinations'] = WriteOffDestinations.objects.all()
        context['storage_types'] = StorageType.objects.exclude(name="Baixa")
        context['shelves'] = Shelf.objects.all()
        context['buildings'] = Building.objects.all()
        context['rooms'] = Rooms.objects.all()
        context['halls'] = Hall.objects.all()
        return context
        
    def post(self, request, *args, **kwargs):
        if 'clean' in request.POST:
            WorkSpace.objects.filter(user=request.user).delete()
            return JsonResponse({'success': 'Produtos removidos com sucesso', 'reload': True}, status=200)
        
        product_id = request.POST.get('product_id')
        remove = request.POST.get('remove')
        write_off_destination_id = request.POST.get('write_off_destination')
        
        if write_off_destination_id:
            write_off_destination = WriteOffDestinations.objects.get(pk=write_off_destination_id)
            for product in WorkSpace.objects.filter(user=request.user):
                product_unit = product.product
                product_unit.write_off = True
                product_unit.save()
                
                if product_unit.shelf:
                    Write_off.objects.create(
                        product_unit=product_unit,
                        origin= product_unit.shelf,
                        storage_type= StorageType.objects.get_or_create(name="Baixa")[0],
                        write_off_date=timezone.now(),
                        observations= "Baixa de produto",
                        write_off_destination = write_off_destination,
                        created_by = request.user,
                    )
                else:
                    Write_off.objects.create(
                        product_unit=product_unit,
                        origin= product_unit.location,
                        storage_type= StorageType.objects.get_or_create(name="Baixa")[0],
                        write_off_date=timezone.now(),
                        observations= "Baixa de produto",
                        write_off_destination =write_off_destination,
                        created_by = request.user,
                    )    
            WorkSpace.objects.filter(user=request.user).delete()
            return JsonResponse({'success': 'Produtos baixados com sucesso', 'reload': True}, status=200)

        if remove:
            try:
                product_id = request.POST.get('remove')
                WorkSpace.objects.filter(user=request.user, product_id=product_id).delete()
                return JsonResponse({'success': 'Produto removido da área de trabalho', 'reload': True}, status=200)
            except ProductUnit.DoesNotExist:
                return JsonResponse({'error': 'Produto nao encontrado'}, status=400)
            
        if product_id:
            try:
                product = ProductUnit.objects.get(pk=product_id)
                if WorkSpace.objects.filter(user=request.user, product=product).exists():
                    return JsonResponse({'error': 'Produto ja está na sua área de trabalho', 'reload' : True}, status=400)
                else:
                    if product.write_off:
                        return JsonResponse({'error': 'Esse produto está baixado', 'reload': True}, status=400)
                    WorkSpace.objects.create(
                        user=request.user,
                        product=product
                    )
                    return JsonResponse({'success': 'Produto adicionado a area de trabalho', 'reload': True}, status=200)
            except ProductUnit.DoesNotExist:
                return JsonResponse({'error': 'Produto nao encontrado'}, status=400)
        
        if request.POST.get('location'):
            location_id = request.POST.get('location')
            building_id = request.POST.get('building')
            room_id = request.POST.get('room')
            hall_id = request.POST.get('hall')
            shelf_id = request.POST.get('shelf')
            observations = request.POST.get('observations')

            destination = StorageType.objects.get(pk=location_id)

            if destination.name == "Depósito":
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
                        transfer_date=date.today(),
                        observations=observations,
                        created_by=request.user,
                    )

                product_unit.location = destination

                if destination.name == "Depósito":
                    product_unit.building_id = building_id
                    product_unit.room_id = room_id
                    product_unit.hall_id = hall_id
                    product_unit.shelf_id = shelf_id
                else:
                    product_unit.building_id = None
                    product_unit.room_id = None
                    product_unit.hall_id = None
                    product_unit.shelf_id = None

                product_unit.save()

            WorkSpace.objects.filter(user=request.user).delete()
            return JsonResponse({'success': 'Produtos transferidos com sucesso', 'transfer': True, 'reload': True}, status=200)


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

class DashboardView(TemplateView):
    template_name = 'admin/dashboard.html'
    
    
from django.contrib import messages


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
                df = pd.read_excel(arquivo, skiprows=1)
                print("Nomes das colunas do DataFrame:", df.columns)  # Adiciona esta linha para inspecionar os nomes das colunas
                df.columns = ['nome', 'preco', 'ncm', 'unidade']

                produtos_adicionados = 0
                produtos_atualizados = 0

                for _, row in df.iterrows():
                    created = self.criar_produto_ou_atualizar(row)
                    if created:
                        produtos_adicionados += 1
                    else:
                        produtos_atualizados += 1

                messages.success(request, f'{produtos_adicionados} produtos foram adicionados e {produtos_atualizados} foram atualizados com sucesso.')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro ao processar o arquivo: {e}')
            
            return redirect('inventory_management:load_data')

        messages.error(request, 'Ocorreu um erro no upload do arquivo. Verifique o formato e tente novamente.')
        return render(request, self.template_name, {'form': form})

    def criar_produto_ou_atualizar(self, row):
        unidade_mapeada = self.MEASURE_MAPPING.get(row['unidade'].upper(), 'u')
        nome_lower = row['nome'].strip().lower()
        produto, created = Product.objects.update_or_create(
            name=nome_lower,
            defaults={
                'ncm': row['ncm'],
                'price': row['preco'],
                'measure': unidade_mapeada,
            }
        )
        return created