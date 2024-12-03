from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Row, Column, Layout
from app.inventory.models import Inventory, InventoryImage, Product


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
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column("Name", css_class="form-group col-3"),
                Column("Category", css_class="form-group col-3"),
                Column("cost", css_class="form-group col-6"),
                Column("Price", css_class="form-group col-6"),
                Column("description", css_class="form-group col-6"),
                Column("barcode", css_class='form-group col-6'),
                Column("model", css_class='form-group col-6'),

            ),
        )
        self.helper.add_input(Submit("submit", "Submit", css_class="btn-primary btn-sm bg-primary"))

    class Meta:
        model = Product
        exclude = ['image_url', 'barcode']


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['location', 'quantity']


class InventoryImageForm(forms.ModelForm):
    image = MultipleFileField()

    class Meta:
        model = InventoryImage
        fields = ['image', ]
