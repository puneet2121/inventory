from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Bill
from .forms import BillForm

from app.purchase.forms import BillForm


# Create your views here.
@login_required
def create_bill(request):
    form = BillForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('purchase:bill_list')
    return render(request, 'purchase/page/bill_create_edit.html', {'form': form})


@login_required
def bill_edit(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    form = BillForm(request.POST or None, instance=bill)
    if form.is_valid():
        form.save()
        return redirect('purchase:bill_list')
    return render(request, 'purchase/page/bill_create_edit.html', {'form': form})


@login_required
def bill_delete(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        bill.delete()
        return redirect('purchase:bill_list')
    return render(request, 'purchase/page/bill_confirm_delete.html', {'bill': bill})


def bill_list(request):
    bills = Bill.objects.all()
    bills = Bill.objects.select_related('paid_to__user').order_by('-bill_date')
    return render(request, 'purchase/page/bill_list.html', {'bills': bills})