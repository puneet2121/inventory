from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from django.db import models
from .models import Bill, PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus, Vendor
from app.purchase.forms import BillForm, PurchaseOrderForm, PurchaseOrderItemFormSet, VendorForm
from ..employee.models import EmployeeProfile


# Create your views here.
@login_required(login_url='/authentication/login/')
def create_bill(request):
    form = BillForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('purchase:bill_list')
    return render(request, 'purchase/page/bill_create_edit.html', {'form': form})

@login_required(login_url='/authentication/login/')
def bill_edit(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    form = BillForm(request.POST or None, instance=bill)
    if form.is_valid():
        form.save()
        return redirect('purchase:bill_list')
    return render(request, 'purchase/page/bill_create_edit.html', {'form': form})

@login_required(login_url='/authentication/login/')
def bill_delete(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == 'POST':
        bill.delete()
        return redirect('purchase:bill_list')
    return render(request, 'purchase/page/bill_confirm_delete.html', {'bill': bill})


@login_required(login_url='/authentication/login/')
def bill_list(request):
    bills = Bill.objects.select_related('paid_to__user').order_by('-bill_date')
    return render(request, 'purchase/page/bill_list.html', {'bills': bills})

# Purchase Orders
@login_required(login_url='/authentication/login/')
def purchase_order_list(request):
    pos = PurchaseOrder.objects.select_related('vendor').prefetch_related('items__product').order_by('-created_at')
    return render(request, 'purchase/page/purchase_order_list.html', {'pos': pos})

@login_required(login_url='/authentication/login/')
def purchase_order_create(request):
    po = PurchaseOrder()
    form = PurchaseOrderForm(request.POST or None, instance=po)
    formset = PurchaseOrderItemFormSet(request.POST or None, instance=po)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        po = form.save()
        formset.instance = po
        formset.save()
        messages.success(request, 'Purchase Order created')
        return redirect('purchase:purchase_order_edit', pk=po.pk)
    return render(request, 'purchase/page/purchase_order_form.html', {
        'form': form,
        'formset': formset,
        'po': po,
        'is_edit': False,
    })

@login_required(login_url='/authentication/login/')
def purchase_order_edit(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if po.status == PurchaseOrderStatus.RECEIVED:
        messages.info(request, 'Received POs cannot be edited.')
        return redirect('purchase:purchase_order_list')
    form = PurchaseOrderForm(request.POST or None, instance=po)
    formset = PurchaseOrderItemFormSet(request.POST or None, instance=po)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Purchase Order updated')
        return redirect('purchase:purchase_order_edit', pk=po.pk)
    return render(request, 'purchase/page/purchase_order_form.html', {
        'form': form,
        'formset': formset,
        'po': po,
        'is_edit': True,
    })

@login_required(login_url='/authentication/login/')
def purchase_order_receive(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == 'POST':
        try:
            total_lines = po.items.count()
            total_qty = po.items.aggregate(t=models.Sum('quantity'))['t'] or 0
            po.receive()
            messages.success(request, f'PO #{po.id} received. {total_qty} units across {total_lines} line(s) added to inventory at {po.location}.')
        except Exception as e:
            messages.error(request, f'Error receiving PO: {e}')
        return redirect('purchase:purchase_order_list')
    return render(request, 'purchase/page/purchase_order_receive_confirm.html', {'po': po})

# Vendors
@login_required(login_url='/authentication/login/')
def vendor_list(request):
    vendors = Vendor.objects.all().order_by('name')
    return render(request, 'purchase/page/vendor_list.html', {'vendors': vendors})

@login_required(login_url='/authentication/login/')
def vendor_create(request):
    form = VendorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vendor created')
        return redirect('purchase:vendor_list')
    return render(request, 'purchase/page/vendor_form.html', {'form': form, 'is_edit': False})


@login_required(login_url='/authentication/login/')
def vendor_edit(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    form = VendorForm(request.POST or None, instance=vendor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vendor updated')
        return redirect('purchase:vendor_list')
    return render(request, 'purchase/page/vendor_form.html', {'form': form, 'is_edit': True, 'vendor': vendor})

@login_required(login_url='/authentication/login/')
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        vendor.delete()
        messages.success(request, 'Vendor deleted')
        return redirect('purchase:vendor_list')
    return render(request, 'purchase/page/vendor_confirm_delete.html', {'vendor': vendor})