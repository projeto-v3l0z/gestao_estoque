from django.views.generic import TemplateView, ListView, DetailView
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
from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models import Max, Sum
from django.core.paginator import Paginator, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect


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
        
        total_meters = product_units.aggregate(total_meters=Sum('weight_length'))['total_meters']
        context['total_meters'] = total_meters if total_meters else 0
        context['product_units'] = product_units_page 
        context['page_obj'] = product_units_page 
        
        return context

class ProductUnitDetailView(DetailView):
    model = ProductUnit
    template_name = 'product_unit_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transfer_areas'] = TransferAreas.objects.all()
        context['shelves'] = Shelf.objects.exclude(pk=self.get_object().location.id)
        context['consumptions'] = ClothConsumption.objects.filter(product_unit=self.get_object())
        context['write_offs'] = Write_off.objects.filter(product_unit=self.get_object())
        context['write_off_destinations'] = WriteOffDestinations.objects.all()
        
        return context
        
    def post(self, request, *args, **kwargs):
        product_unit = self.get_object()

        if 'write_off' in request.POST:
            product_unit.write_off = True
            write_off_destination_id = request.POST.get('write_off_destination')
            write_off_destination = WriteOffDestinations.objects.get(pk=write_off_destination_id)
            
            if product_unit.shelf:
                Write_off.objects.create(
                    product_unit=product_unit,
                    origin= product_unit.shelf,
                    transfer_area= TransferAreas.objects.get_or_create(name="Baixa")[0],
                    write_off_date=timezone.now(),
                    observations= "Baixa de produto",
                    write_off_destination = write_off_destination
                )
            else:
                Write_off.objects.create(
                    product_unit=product_unit,
                    origin= product_unit.location,
                    transfer_area= TransferAreas.objects.get_or_create(name="Baixa")[0],
                    write_off_date=timezone.now(),
                    observations= "Baixa de produto",
                    write_off_destination =write_off_destination
                )    
            
        elif request.POST.get('back_to_stock') == 'True':
            product_unit.write_off = False
            last_write_off = Write_off.objects.filter(product_unit=product_unit).aggregate(last_write_off_date=Max('write_off_date'))
            last_write_off_date = last_write_off.get('last_write_off_date')

            if last_write_off_date:
                last_write_off = Write_off.objects.filter(product_unit=product_unit, write_off_date=last_write_off_date).first()
                write_off_destination = last_write_off.write_off_destination if last_write_off.write_off_destination else None
            else:
                write_off_destination = None

            location_id = request.POST.get('location')
            location = TransferAreas.objects.get(pk=location_id)
            shelf_id = request.POST.get('shelf')

            if shelf_id != None:
                shelf = Shelf.objects.get(pk=shelf_id)

            
                Write_off.objects.create(
                        product_unit=product_unit,
                        origin=TransferAreas.objects.get_or_create(name="Baixa")[0],
                        transfer_area=location,
                        destination=shelf,
                        write_off_date=timezone.now(),
                        observations="Retorno ao estoque",
                        write_off_destination=write_off_destination, 
                )
                product_unit.location = location
                product_unit.shelf = shelf
            else:
                Write_off.objects.create(
                    product_unit=product_unit,
                    origin=TransferAreas.objects.get_or_create(name="Baixa")[0],
                    transfer_area=location,
                    write_off_date=timezone.now(),
                    observations="Retorno ao estoque",
                   write_off_destination=write_off_destination, 
                )
                product_unit.location = location
                product_unit.shelf = None
        else:
            destination_id = request.POST.get('destination')
            observations = request.POST.get('observations')
            
            origin = product_unit.location
            destination = Shelf.objects.get(pk=destination_id)
            
            StockTransfer.objects.create(
                product_unit=product_unit,
                origin=origin,
                destination=destination,
                transfer_date=date.today(),
                observations=observations,
            )
            
            product_unit.location = destination

        consumption = request.POST.get('remainder')
        if consumption:
                consumption_decimal = Decimal(consumption)

                if consumption_decimal > product_unit.weight_length:
                    return JsonResponse({'remainder': "O consumo não pode ser maior que o peso/tamanho antes da subtração."}, status=400)
                
                remainder = consumption_decimal
                if remainder < 0:
                    return JsonResponse({'remainder': "O peso/tamanho depois da subtração não pode ser negativo."}, status=400)
                
                try:
                    ClothConsumption.objects.create(
                        product_unit=product_unit,
                        weight_length_before=product_unit.weight_length,
                        remainder= consumption_decimal
                    )
                except ValidationError as e:
                    return JsonResponse({'remainder': e.message}, status=400)


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


class GetProductLocationView(View):
    def get(self, request, *args, **kwargs):
        product_unit = ProductUnit.objects.get(slug=self.kwargs.get('slug'))
        return JsonResponse({'location': str(product_unit.location.slug)})
    
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
                    qr_codes.append(qr)

                
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

                for idx, qr in enumerate(qr_codes):
                    row = idx // columns  
                    col = idx % columns  
                    page_idx = idx // items_per_page 
                   
                    if size_preset == 'pequeno':
                        y_coordinate = page_height - 200 - (row % (items_per_page // columns)) * (qr_size + 20)
                        x_coordinate = 27 + x_offset + col * (qr_size + 20)
                    elif size_preset == 'medio':
                        y_coordinate = page_height - 200- (row % (items_per_page // columns)) * (qr_size + 20)
                        x_coordinate = 13 + x_offset + col * (qr_size + 20)
                    elif size_preset == 'grande':
                        y_coordinate = page_height - 250 - (row % (items_per_page // columns)) * (qr_size + 20)
                        x_coordinate = 50 + x_offset + col * (qr_size + 20)

                    
                    if idx > 0 and idx % items_per_page == 0:
                        c.showPage()

                    c.drawInlineImage(qr, x_coordinate, y_coordinate, width=qr_size, height=qr_size)

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
        
    def post(self, request, *args, **kwargs):
        if 'clean' in request.POST:
            WorkSpace.objects.filter(user=request.user).delete()
            return HttpResponseRedirect(reverse('inventory_management:workspace'))
        
        product_id = request.POST.get('product_id')

        if not product_id:
            return JsonResponse({'error': 'ID de produto inválido'}, status=400)
        
        if product_id:
            try:
                product = ProductUnit.objects.get(pk=product_id)
                if WorkSpace.objects.filter(user=request.user, product=product).exists():
                    return JsonResponse({'error': 'Produto ja adicionado a area de trabalho', 'reload' : True}, status=400)
                else:
                    WorkSpace.objects.create(
                        user=request.user,
                        product=product
                    )
                    return JsonResponse({'success': 'Produto adicionado à área de trabalho', 'reload': True}, status=200)
            except ProductUnit.DoesNotExist:
                return JsonResponse({'error': 'Produto nao encontrado'}, status=400)
            
        