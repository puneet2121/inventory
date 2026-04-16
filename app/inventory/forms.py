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


class InventoryImageUploadForm(forms.Form):
    images = MultipleFileField(required=False, label="Upload photos")
    image_urls = forms.CharField(
        required=False,
        label="Existing S3 URLs or keys",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'https://bucket.s3.region.amazonaws.com/folder/img-1.jpg\nsecond-image.jpg'
        }),
        help_text="One per line. Relative keys are prefixed with your PUBLIC_MEDIA_BASE_URL."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


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

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class importInventoryForm(forms.Form):
    """
    Form for uploading CSV(s) to import inventory in bulk.

    - file: Accepts one or more CSV files. Use request.FILES.getlist('file') in the view.
    - update_existing: If True, existing products (matched by SKU) will be updated; otherwise skipped or duplicated based on view logic.
    """
    file = forms.FileField(
        label="CSV file",
        help_text="Upload a CSV file with headers: name, sku, category, price, stock. You can select multiple files.",
        widget=MultipleFileInput(attrs={
            "accept": ".csv,text/csv",
            "multiple": True,
            "class": "form-control",
        })
    )
    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        label="Update existing products",
        help_text="When checked, rows with an SKU matching an existing product will update that product."
    )

    def clean_file(self):
        """
        Basic validation: ensure at least one file and that each file looks like a CSV.
        Deeper validation (headers, encoding) should be done in the view where files are read.
        """
        uploaded = self.files.getlist('file') if hasattr(self, 'files') else None
        if not uploaded:
            # Fall back to single file upload retrieval
            uploaded_single = self.cleaned_data.get('file')
            if uploaded_single:
                return [uploaded_single]
            raise forms.ValidationError("No file uploaded.")
        # Basic checks
        cleaned_files = []
        for f in uploaded:
            # Check content type heuristically; browser may not always set it
            ct = getattr(f, 'content_type', '') or ''
            if ct and 'csv' not in ct and 'text' not in ct:
                # allow through but warn via validation error
                raise forms.ValidationError(f"Uploaded file {f.name} does not look like a CSV.")
            if f.size == 0:
                raise forms.ValidationError(f"Uploaded file {f.name} is empty.")
            cleaned_files.append(f)
        return cleaned_files

    def __init__(self, *args, **kwargs):
        """
        Configure crispy forms helper so the form renders nicely if used in templates.
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.attrs = {'enctype': 'multipart/form-data'}
        self.helper.add_input(Submit('submit', 'Upload', css_class='btn-primary'))
