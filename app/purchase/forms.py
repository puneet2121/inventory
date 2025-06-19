# purchases/forms.py
from django import forms
from .models import Bill


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['amount', 'bill_date', 'category', 'vehicle', 'paid_to', 'notes']
        widgets = {
            'bill_date': forms.DateInput(attrs={'type': 'date'}),
        }