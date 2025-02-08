from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from .forms import EmployeeForm
from .models import EmployeeProfile


@login_required(login_url='/authentication/login/')
@permission_required('employee.add_employeeprofile', raise_exception=True)
def create_or_edit_employee(request, pk=None):
    if pk:
        employee = get_object_or_404(EmployeeProfile, pk=pk)  # Get existing employee for editing
    else:
        employee = None  # Create a new employee if pk is not provided

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)  # Use instance for editing
        if form.is_valid():
            form.save()
            return redirect('employee_list')  # Redirect after saving
    else:
        form = EmployeeForm(instance=employee)  # Pre-fill form for editing

    return render(request, 'employee/page/create_employee.html', {'form': form})


@login_required(login_url='/authentication/login/')
def employee_list(request):
    employees = EmployeeProfile.objects.select_related('user').all()
    return render(request, 'employee/page/employee_list_page.html', {'employees': employees})


@login_required(login_url='/authentication/login/')
@permission_required('employee.delete_employeeprofile', raise_exception=True)
def delete_employee(request, pk):
    employee = get_object_or_404(EmployeeProfile, pk=pk)  # Fetch the employee
    employee.delete()  # Delete the record
    return redirect('employee:employee_list')  # Redirect back to the list