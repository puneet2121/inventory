# purchases/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Bill, PurchaseOrder, PurchaseOrderItem, Vendor
from app.inventory.models import Product


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['amount', 'bill_date', 'category', 'vehicle', 'paid_to', 'notes']
        widgets = {
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
        }


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['vendor', 'location', 'note']


class PurchaseOrderItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all())

    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_price']


PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    fields=['product', 'quantity', 'unit_price'],
    extra=1,
    can_delete=True
)


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'contact', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }