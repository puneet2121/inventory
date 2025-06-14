import openpyxl
from django.contrib import messages
from django.core.files.storage import default_storage
from django.db.models import F
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from app.inventory.forms import ProductForm, InventoryImageForm, InventoryForm, CategoryForm
from app.inventory.models import Inventory, InventoryImage, Category
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import pandas as pd
import requests
from django.shortcuts import render


@login_required(login_url='/authentication/login/')
def index(request):
    context = {
        'message': 'Hello World!'
    }
    return render(request, 'inventory/page/product_index_page.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Inventory


@login_required(login_url='/authentication/login/')
def create_or_edit_product_info(request, product_id=None):
    product_instance = get_object_or_404(Product, pk=product_id) if product_id else None
    inventory_instance = None

    if product_instance:
        try:
            inventory_instance = Inventory.objects.get(product=product_instance)
        except Inventory.DoesNotExist:
            pass

    if request.method == 'POST':
        product_form = ProductForm(request.POST, instance=product_instance)
        inventory_form = InventoryForm(request.POST, instance=inventory_instance)

        if product_form.is_valid() and inventory_form.is_valid():
            try:
                product = product_form.save()
                inventory = inventory_form.save(commit=False)
                inventory.product = product
                inventory.save()

                messages.success(request, 'Product saved successfully!')
                return redirect('inventory:item_list')
            except Exception as e:
                messages.error(request, f'Error saving product: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        product_form = ProductForm(instance=product_instance)
        inventory_form = InventoryForm(instance=inventory_instance)

    context = {
        'product_form': product_form,
        'inventory_form': inventory_form,
        'product_id': product_id,
        'is_edit': product_id is not None
    }

    return render(request, 'inventory/page/product_upload_page.html', context)

@login_required(login_url='/authentication/login/')
def item_list_view(request):
    products = Product.objects.all()  # Fetch all products
    inventory_data = Inventory.objects.all()  # Fetch inventory data

    # Create a mapping of product to stock
    product_inventory = {}
    for inventory in inventory_data:
        product_id = inventory.product.id
        if product_id in product_inventory:
            product_inventory[product_id] += inventory.quantity
        else:
            product_inventory[product_id] = inventory.quantity

    # Add stock data to products
    product_list = [
        {
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'cost': product.cost,
            'price': product.price,
            'stock': product_inventory.get(product.id, 0)
        }
        for product in products
    ]
    products = Product.objects.all()


    context = {
        'products': product_list,
        'total_items': products.count(),
        'low_stock_count': products.filter(inventory__lte=5).count(),  # Changed to fixed value of 5
    }

    return render(request, 'inventory/page/item_list_page.html', context)


@login_required(login_url='/authentication/login/')
def product_delete_view(request, product_id):
    product = get_object_or_404(Inventory, pk=product_id)
    product.delete()
    messages.success(request, 'Product Deleted Successfully!')
    return redirect('inventory:product_list')


@login_required(login_url='/authentication/login/')
def upload_images(request, product_id):
    InventoryImageFormSet = inlineformset_factory(Inventory, InventoryImage,
                                                  form=InventoryImageForm, extra=1)
    inventory_instance = get_object_or_404(Inventory, pk=product_id)

    if request.method == 'POST':
        formset = InventoryImageFormSet(request.POST, request.FILES, instance=inventory_instance)
        if formset.is_valid():

            for form in formset.forms:
                if form.cleaned_data:
                    for image in form.cleaned_data['image']:
                        file_path = default_storage.save(image.name, image)
                        full_s3_url = settings.MEDIA_URL + file_path
                        inventory_image = InventoryImage(inventory=inventory_instance, image=image, image_url=full_s3_url)
                        inventory_image.save()
            messages.success(request, 'Product Created Successfully!')
            return redirect('inventory:edit_product', product_id=product_id)
        else:
            print("Formset Errors:", formset.errors)

    else:
        formset = InventoryImageFormSet()

    return render(request, 'inventory/page/image_upload.html', {'formset': formset})

@login_required(login_url='/authentication/login/')
def export_inventory(request):
    # Create a workbook and select active worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventory"

    # Add header row
    headers = [
        "Product Name", "Category", "Cost", "Price",
        "Price A", "Price B", "Description",
        "Location", "Quantity",
    ]
    ws.append(headers)

    # Query inventory and product data
    inventory_items = Inventory.objects.select_related('product').all()

    # Populate rows
    for item in inventory_items:
        ws.append([
            item.product.name,
            item.product.category,
            item.product.cost,
            item.product.price,
            item.product.price_A,
            item.product.price_B,
            item.product.description,
            item.location,
            item.quantity,

        ])

    # Create response with content type for Excel
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response['Content-Disposition'] = 'attachment; filename=inventory.xlsx'
    wb.save(response)
    return response


@login_required(login_url='/authentication/login/')
def import_inventory(request):
    if request.method == "POST" and 'file' in request.FILES:
        file = request.FILES['file']
        if not file.name.endswith('.xlsx'):
            messages.error(request, "Please upload a valid Excel (.xlsx) file.")
            return redirect('inventory:list_inventory')

        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active

            for row in ws.iter_rows(min_row=2, values_only=True):  # Skip header row
                # Extract only the required columns
                try:
                    name, category, price, quantity = row[:4]  # Limit to the first 4 columns

                    # Validate the data
                    if not (name and category and price and quantity):
                        continue  # Skip rows with missing essential data

                    # Get or create Product
                    product, created = Product.objects.get_or_create(
                        name=name,
                        defaults={"category": category, "price": price},
                    )
                    if not created:
                        product.category = category
                        product.price = price
                        product.save()

                    # Update or create Inventory for the product
                    Inventory.objects.update_or_create(
                        product=product,
                        defaults={"quantity": quantity},
                    )
                except ValueError as e:
                    # Handle specific row errors (e.g., too few or invalid values)
                    continue

            messages.success(request, "Inventory imported successfully!")
        except Exception as e:
            messages.error(request, f"Error during import: {str(e)}")
        return redirect('inventory:item_list')

    messages.error(request, "No file selected or invalid request.")
    return redirect('inventory:item_list')


@login_required
def category_list(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'inventory/page/category_list_page.html', context)


@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm()

    return render(request, 'inventory/page/category_form.html', {
        'form': form,
        'is_add': True
    })


@login_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'inventory/page/category_form.html', {
        'form': form,
        'category': category,
        'is_add': False
    })


@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        try:
            category.delete()
            messages.success(request, 'Category deleted successfully!')
        except Exception as e:
            messages.error(request, 'Cannot delete category. It has associated products.')
    return redirect('inventory:category_list')