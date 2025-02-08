from django import forms
from .models import SalesOrder, OrderItem
from app.customers.models import Customer
from app.inventory.models import Product
from app.employee.models import EmployeeProfile


class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['customer', 'customer_name', 'customer_type', 'employee']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_type': forms.Select(attrs={'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all()
        self.fields['customer'].empty_label = "Select a customer (optional)"
        self.fields['customer_name'].required = False  # Make it optional
        self.fields['customer_name'].widget.attrs['placeholder'] = "Enter customer name for walk-in"
        self.fields['employee'].queryset = EmployeeProfile.objects.all()
        self.fields['employee'].empty_label = "Select an employee"
    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        customer_name = cleaned_data.get('customer_name')
        customer_type = cleaned_data.get('customer_type')
        employee = cleaned_data.get('employee')

        if customer_type == 'registered' and not customer:
            raise forms.ValidationError("A registered customer must be selected.")
        if customer_type == 'walk_in' and not customer_name:
            raise forms.ValidationError("Customer name is required for walk-in customers.")
        return cleaned_data


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.all()
        self.fields['product'].empty_label = "Select a product"
        self.fields['quantity'].widget.attrs['placeholder'] = "Enter quantity"

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if product and quantity:
            inventory = getattr(product, 'inventory', None)
            if inventory and inventory.quantity < quantity:
                raise forms.ValidationError(
                    f"Not enough inventory for {product.name}. Available: {inventory.quantity}"
                )
        return cleaned_data
