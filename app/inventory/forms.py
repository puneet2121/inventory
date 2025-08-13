from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Row, Column, Layout, Div, Button, HTML, Field
from app.inventory.models import Inventory, InventoryImage, Product
from .models import Category
from app.core.tenant_middleware import get_current_tenant


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
                  'description', 'barcode', 'model', 'sku', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure category dropdown shows current tenant categories and any legacy NULL-tenant ones
        tenant_id = get_current_tenant()
        try:
            # Use base manager to bypass tenant filter so we can include NULLs, then scope explicitly
            if tenant_id is not None:
                self.fields['category'].queryset = Category._base_manager.filter(tenant_id__in=[tenant_id, None]).order_by('name')
            else:
                # Fallback: show only NULL-tenant categories if no tenant in context
                self.fields['category'].queryset = Category._base_manager.filter(tenant_id__isnull=True).order_by('name')
        except Exception:
            # In case of unexpected issues, default to tenant-aware manager
            self.fields['category'].queryset = Category.objects.all().order_by('name')
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
                    Div('sku', css_class='form-group mb-3'),
                    Div('expiry_date', css_class='form-group mb-3'),
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
        fields = ['quantity', 'location']

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
