from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Row, Column, Layout, Div, Button, HTML
from app.inventory.models import Inventory, InventoryImage, Product
from .models import Category


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'cost', 'price',
                  'description', 'barcode', 'model']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Don't render form tag as we'll handle it in template
        self.helper.layout = Layout(
            Div(
                # Basic Information Section
                HTML('<h5 class="section-title">Basic Information</h5>'),
                Div(
                    Div('name', css_class='form-group mb-3'),
                    Div('category', css_class='form-group mb-3'),
                    Div('model', css_class='form-group mb-3'),
                    Div('barcode', css_class='form-group mb-3'),
                    css_class='col-md-6'
                ),
                # Pricing Section
                Div(
                    HTML('<h5 class="section-title">Pricing Information</h5>'),
                    Div('cost', css_class='form-group mb-3'),
                    Div('price', css_class='form-group mb-3'),
                    css_class='col-md-6'
                ),
                css_class='row'
            ),
            # Description Section
            Div(
                HTML('<h5 class="section-title mt-3">Description</h5>'),
                Div('description', css_class='form-group'),
                css_class='col-12'
            ),
        )


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['quantity','location']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div('quantity', css_class='form-group'),
                css_class='col-md-6'
            ),
            Div('location'),
        )


class InventoryImageForm(forms.ModelForm):
    image = MultipleFileField()

    class Meta:
        model = InventoryImage
        fields = ['image', ]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter category description'
            }),
        }
