from django.shortcuts import render, get_object_or_404, redirect
from .models import Customer
from .forms import CustomerForm


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
    return render(request, 'customers/page/list_customers.html', {'customers': customers})


def customers_with_debt(request):
    customers = Customer.objects.filter(debt__gt=0)
    return render(request, 'customers/page/customers_with_debt.html', {'customers': customers})
