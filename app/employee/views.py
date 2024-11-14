from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from app.employee.forms import EmployeeForm
from app.employee.models import Profile

@login_required(login_url='/authentication/login/')
def create_or_edit_employee_info(request, employee_id=None):
    # Retrieve or create a Profile instance
    if employee_id:
        instance = get_object_or_404(Profile, pk=employee_id)
    else:
        instance = None

    # Process the form data
    if request.method == 'POST':
        employee_form = EmployeeForm(request.POST, request.FILES, instance=instance)
        if employee_form.is_valid():
            instance = employee_form.save()
            messages.success(request, 'Employee information saved successfully!')

            # Determine redirection based on button clicked
            if 'next' in request.POST:
                return redirect('inventory:upload_images', product_id=instance.pk)
            elif 'save_later' in request.POST:
                return redirect('inventory:product_list')
    else:
        employee_form = EmployeeForm(instance=instance)

    # Render the form
    return render(request, 'employee/page/product_upload_page.html', {'form': employee_form, 'employee_id': employee_id})


@login_required(login_url='/authentication/login/')
def employee_list_view(request):
    products = User.objects.all()
    return render(request, 'employee/page/employee_list_page.html', {'products': products})
