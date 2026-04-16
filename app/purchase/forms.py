# purchases/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Bill, PurchaseOrder, PurchaseOrderItem, Vendor
from app.inventory.models import Product
from app.core.tenant_middleware import get_current_tenant
from app.employee.models import EmployeeProfile


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['amount', 'bill_date', 'category', 'vehicle', 'paid_to', 'notes']
        widgets = {
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenant_id = get_current_tenant()
        if tenant_id is not None and 'paid_to' in self.fields:
            self.fields['paid_to'].queryset = EmployeeProfile.objects.filter(tenant_id=tenant_id).order_by('user__username')


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['vendor', 'location', 'note']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenant_id = get_current_tenant()
        vendor_field = self.fields.get('vendor')
        if vendor_field is None:
            return
        if tenant_id is not None:
            vendor_field.queryset = Vendor.objects.filter(tenant_id=tenant_id).order_by('name')
        else:
            vendor_field.queryset = Vendor.objects.none()


class PurchaseOrderItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.none())

    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenant_id = get_current_tenant()
        if tenant_id is not None:
            self.fields['product'].queryset = Product.objects.filter(tenant_id=tenant_id).order_by('name')
        else:
            self.fields['product'].queryset = Product.objects.none()


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
