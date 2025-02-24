from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from app.customers.models import Customer
from app.customers.forms import CustomerForm


def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_customers')
    else:
        form = CustomerForm()
    return render(request, 'customers/page/add_customer.html', {'form': form})


def list_customers(request):
    customers = Customer.objects.all()
    total_customers = customers.count()  # Count the total number of customers
    total_debt = customers.aggregate(total_debt=Sum('total_debt')) or 0
    return render(request, 'customers/page/list_customers.html', {
        'customers': customers,
        'total_customers': total_customers,
        'total_debt': total_debt,
    })


def customers_with_debt(request):
    customers = Customer.objects.filter(debt__gt=0)
    return render(request, 'customers/page/customers_with_debt.html', {'customers': customers})
