# forms.py
from django import forms
from .models import Product, Building, ProductUnit, Hall, Rooms, Shelf
from django_select2 import forms as s2forms

class QRCodeForm(forms.Form):
    SIZE_PRESETS = [
            ('pequeno', 'Pequeno'),
            ('medio', 'Médio'),
            ('grande', 'Grande'),
        ]
    size_preset = forms.ChoiceField(label='Tamanho', choices=SIZE_PRESETS, widget=forms.Select(attrs={'style': 'width: 300px;', 'class': 'form-select'}))


class DashboardFilterForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=False, label="Produto")
    building = forms.ModelChoiceField(queryset=Building.objects.all(), required=False, label="Depósito")

class UploadExcelForm(forms.Form):
    file = forms.FileField(label='Arquivo Excel', widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        if file:
            if not file.name.endswith('.xlsx'):
                raise forms.ValidationError('O arquivo deve ser um arquivo Excel (.xlsx)')
        return cleaned_data
    
class ProductWidget(s2forms.HeavySelect2Widget):
    data_view = 'inventory_management:product-autocomplete'

class ProductUnitForm(forms.ModelForm):
    product = forms.CharField(widget=ProductWidget(attrs={'style': 'width: 300px;'}))

    class Meta:
        model = ProductUnit
        exclude = ['qr_code_generated', 'was_written_off', 'write_off', 'hall', 'room', 'shelf', 'building']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código'}),
            'provider': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fornecedor'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantidade'}),
            'weight_length': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Peso/Comprimento'}),
            'incoming': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Entrada'}),
        }
    
    def clean_product(self):
        product_id = self.data.get('product')
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise forms.ValidationError("Produto inválido")


class ProductCreateForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['color','color_id','created_by','created_at','update_by','update_at','created_by_id','id','productunit','slug','updated_by_id','pattern','patternn_id']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'nome'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'descrição'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'preço'}),
            'measure': forms.Select(choices=Product.MEASURE_CHOICES, attrs={'class': 'form-control', 'placeholder': 'medida'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'largura'}),
            'composition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'composição'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'placeholder': 'imagem'}),
            'ncm': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ncm'}),
            'code1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'código 1'}),
            'code2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'código 2'}),
        }
        
