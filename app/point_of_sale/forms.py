from django import forms
from django.forms import inlineformset_factory
from .models import SalesOrder, OrderItem, Payment
from app.customers.models import Customer
from app.inventory.models import Product
from app.employee.models import EmployeeProfile
from django.db import models


class SalesOrderForm(forms.ModelForm):
    customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter customer name for walk-in'
        })
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add any notes about this order...'
        })
    )

    class Meta:
        model = SalesOrder
        fields = ['customer', 'customer_type', 'employee', 'note']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'x-model': 'selectedCustomer',
                '@change': 'handleCustomerChange()'
            }),
            'customer_type': forms.Select(attrs={
                'class': 'form-select',
                'x-model': 'customerType'
            }),
            'employee': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all()
        self.fields['customer'].empty_label = "Select a customer (optional)"
        self.fields['employee'].queryset = EmployeeProfile.objects.all()
        self.fields['employee'].empty_label = "Select an employee"
        self.fields['customer'].required = False
        self.fields['employee'].required = False

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        customer_name = cleaned_data.get('customer_name')
        customer_type = cleaned_data.get('customer_type')

        if customer_type == 'registered' and not customer:
            raise forms.ValidationError("A registered customer must be selected.")
        if customer_type == 'walk_in' and not customer_name:
            raise forms.ValidationError("Customer name is required for walk-in customers.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        customer_type = self.cleaned_data.get('customer_type')
        customer_name = self.cleaned_data.get('customer_name')

        if customer_type == 'walk_in' and customer_name:
            # Try to reuse or create a walk-in customer
            customer, created = Customer.objects.get_or_create(
                name=customer_name.strip(),
                defaults={
                    'city': 'Walk-in',
                    'customer_type': 'C',
                    'contact': '0000000000'
                }
            )
            instance.customer = customer

        # Auto-generate order number if not present
        if not instance.order_number:
            last_order = SalesOrder.objects.order_by('-id').first()
            next_number = (last_order.id + 1) if last_order else 1
            instance.order_number = f"SO-{next_number:05d}"

        if commit:
            instance.save()
        return instance


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


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Enter payment amount'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].required = True
        self.fields['payment_method'].required = True

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class RefundForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'reference']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Enter refund amount',
                'type': 'number'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter reference number or note'
            })
        }

    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        self.fields['amount'].required = True
        self.fields['payment_method'].required = True
        self.fields['reference'].required = False
        
        # Set initial values if provided
        if self.invoice:
            # Calculate available amount for refund
            total_paid = self.invoice.payments.filter(type='payment').aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            
            total_refunded = self.invoice.payments.filter(type='refund').aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            
            available_for_refund = total_paid - total_refunded
            
            # Set max value for amount field
            self.fields['amount'].widget.attrs['max'] = str(available_for_refund)
            
            print(f"Form initialized with available_for_refund: {available_for_refund}")
            print(f"Amount field widget attrs: {self.fields['amount'].widget.attrs}")

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        print(f"Cleaning amount: {amount}, type: {type(amount)}")
        
        if amount and amount <= 0:
            raise forms.ValidationError("Refund amount must be greater than zero.")
        
        if self.invoice:
            # Get total paid amount (excluding previous refunds)
            total_paid = self.invoice.payments.filter(type='payment').aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            
            # Get total refunded amount
            total_refunded = self.invoice.payments.filter(type='refund').aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            
            # Available amount for refund
            available_for_refund = total_paid - total_refunded
            
            print(f"Total paid: {total_paid}, Total refunded: {total_refunded}, Available: {available_for_refund}")
            
            if amount > available_for_refund:
                raise forms.ValidationError(
                    f"Refund amount cannot exceed the available amount (₹{available_for_refund:.2f})."
                )
        
        return amount


# Create the formset for order items
OrderItemFormSet = inlineformset_factory(
    SalesOrder,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
    fields=['product', 'quantity', 'price']
)
