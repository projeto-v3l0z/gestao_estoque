# forms.py
from django import forms
from .models import Product, Building, ProductUnit

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
    
    

class ProductUnitForm(forms.ModelForm):
    class Meta:
        model = ProductUnit
        exclude = ['qr_code_generated', 'was_written_off', 'write_off','provider', 'building', 'room', 'hall', 'shelf']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'provider': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.HiddenInput(),
            'building': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'hall': forms.Select(attrs={'class': 'form-control'}),
            'shelf': forms.Select(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'incoming': forms.NumberInput(attrs={'class': 'form-control'}),
        }