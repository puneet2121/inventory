from django import forms
from .models import SalesOrder
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['product', 'quantity', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('product', css_class='form-group col-md-6 mb-0'),
                Column('quantity', css_class='form-group col-md-3 mb-0'),
                Column('price', css_class='form-group col-md-3 mb-0'),
                css_class='row'
            ),
            Submit('submit', 'Submit Order', css_class='btn btn-primary mt-3')
        )
