from django import forms
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from app.point_of_sale.models import SalesOrder
from app.customers.models import Customer


class SalesReportForm(forms.Form):
    REPORT_TYPES = [
        ('summary', 'Sales Summary'),
        ('detailed', 'Detailed Sales'),
        ('product_wise', 'Product Wise Sales'),
        ('customer_wise', 'Customer Wise Sales'),
    ]
    
    DATE_RANGES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_year', 'This Year'),
        ('custom', 'Custom Range'),
    ]
    
    # Report type selection
    report_type = forms.ChoiceField(
        label='Report Type',
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        initial='summary'
    )
    
    # Date range selection
    date_range = forms.ChoiceField(
        label='Date Range',
        choices=DATE_RANGES,
        widget=forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleCustomDateRange(this.value)'}),
        required=True,
        initial='this_month'
    )
    
    # Custom date range fields
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control',
            'id': 'start_date'
        }),
        required=False
    )
    
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control',
            'id': 'end_date'
        }),
        required=False
    )
    
    # Customer filter
    customer = forms.ModelChoiceField(
        label='Customer',
        queryset=Customer.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'Select a customer (optional)'
        }),
        required=False
    )
    
    # # Status filter
    # STATUS_CHOICES = [
    #     ('', 'All Statuses'),
    #     *SalesOrder.status
    # ]
    #
    # status = forms.ChoiceField(
    #     label='Order Status',
    #     choices=STATUS_CHOICES,
    #     widget=forms.Select(attrs={'class': 'form-select'}),
    #     required=False
    # )
    
    # Output format
    OUTPUT_FORMATS = [
        ('html', 'View in Browser'),
        ('pdf', 'Download as PDF'),
        ('csv', 'Download as CSV'),
    ]
    
    output_format = forms.ChoiceField(
        label='Output Format',
        choices=OUTPUT_FORMATS,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='html',
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date range (current month)
        today = timezone.now().date()
        first_day = today.replace(day=1)
        self.fields['start_date'].initial = first_day
        self.fields['end_date'].initial = today
        
        # Set customer queryset to be ordered by name
        self.fields['customer'].queryset = Customer.objects.all().order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if date_range == 'custom' and (not start_date or not end_date):
            raise forms.ValidationError('Please select both start and end dates for custom range.')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('Start date cannot be after end date.')
            
        return cleaned_data
    
    def get_date_range(self):
        """Return start and end dates based on the selected range"""
        date_range = self.cleaned_data.get('date_range')
        today = timezone.now().date()
        
        if date_range == 'custom':
            return self.cleaned_data['start_date'], self.cleaned_data['end_date']
        
        if date_range == 'today':
            return today, today
        elif date_range == 'yesterday':
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif date_range == 'this_week':
            start = today - timedelta(days=today.weekday())
            return start, today
        elif date_range == 'last_week':
            end = today - timedelta(days=today.weekday() + 1)
            start = end - timedelta(days=6)
            return start, end
        elif date_range == 'this_month':
            start = today.replace(day=1)
            return start, today
        elif date_range == 'last_month':
            first_day = today.replace(day=1)
            last_month_end = first_day - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return last_month_start, last_month_end
        elif date_range == 'this_year':
            start = today.replace(month=1, day=1)
            return start, today
        
        # Default to current month
        start = today.replace(day=1)
        return start, today
