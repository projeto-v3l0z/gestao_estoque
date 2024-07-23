# forms.py
from django import forms
from .models import Product, Building

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