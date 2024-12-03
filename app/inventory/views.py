from django.contrib import messages
from django.core.files.storage import default_storage
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from app.inventory.forms import ProductForm, InventoryImageForm, InventoryForm
from app.inventory.models import Inventory, InventoryImage
from django.conf import settings
from django.contrib.auth.decorators import login_required
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
    # Check if we are editing a product or creating a new one
    product_instance = get_object_or_404(Product, pk=product_id) if product_id else None
    inventory_instance = None

    if product_instance:
        try:
            inventory_instance = Inventory.objects.get(product=product_instance)
        except Inventory.DoesNotExist:
            inventory_instance = None

    if request.method == 'POST':
        # Initialize both forms with POST data
        product_form = ProductForm(request.POST, request.FILES, instance=product_instance)
        inventory_form = InventoryForm(request.POST, instance=inventory_instance)

        if product_form.is_valid() and inventory_form.is_valid():
            # Save product first
            product = product_form.save()

            # Save inventory and associate it with the product
            inventory = inventory_form.save(commit=False)
            inventory.product = product
            inventory.save()

            messages.success(request, 'Product information saved successfully!')

            return redirect('inventory:product_list')

            # if 'next' in request.POST:
            #     return redirect('inventory:upload_images', product_id=product.pk)
            # elif 'save_later' in request.POST:
            #     return redirect('inventory:product_list')
    else:
        # Initialize both forms for GET requests
        product_form = ProductForm(instance=product_instance)
        inventory_form = InventoryForm(instance=inventory_instance)

    # Pass both forms to the template
    return render(
        request,
        'inventory/page/product_upload_page.html',
        {
            'product_form': product_form,
            'inventory_form': inventory_form,
            'product_id': product_id,
        },
    )


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

    context = {
        'products': product_list,
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
