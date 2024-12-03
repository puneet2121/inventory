from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from app.point_of_sale.models import SalesOrder, OrderItem
from app.customers.models import Customer
from app.inventory.models import Product


class SalesOrderForm(forms.ModelForm):
    # Extra fields for order items
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Product",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.IntegerField(
        label="Quantity",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )
    price = forms.DecimalField(
        label="Price per Unit",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    customer_name = forms.CharField(
        required=False,
        label="Other Customer (Optional)",
        widget=forms.TextInput(attrs={'placeholder': 'Enter customer name'}),
    )

    class Meta:
        model = SalesOrder
        fields = ['customer', 'product', 'quantity', 'price', 'paid_amount', 'payment_method']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('customer'),
            Field('customer_name', css_class='d-none', id='other-customer-field'),
            Field('product'),
            Field('quantity'),
            Field('price'),
            Field('paid_amount'),
            Field('payment_method'),
            Submit('submit', 'Submit Order', css_class='btn btn-primary'),
        )
        self.fields['customer'].queryset = Customer.objects.all()
        self.fields['customer'].empty_label = "Select Customer"

    def save(self, commit=True):
        """Save the sales order and create associated order items."""
        sales_order = super().save(commit=False)
        if self.cleaned_data.get('customer_name'):
            sales_order.customer_name = self.cleaned_data['customer_name']
        if commit:
            sales_order.save()

            # Create associated OrderItem
            product = self.cleaned_data['product']
            quantity = self.cleaned_data['quantity']
            price = self.cleaned_data['price']
            total_price = quantity * price

            order_item = OrderItem(
                sales_order=sales_order,
                product=product,
                quantity=quantity,
                price=price,
                total_price=total_price
            )
            order_item.save()

        return sales_order
