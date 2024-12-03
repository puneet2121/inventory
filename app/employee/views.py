from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from .forms import EmployeeForm
from .models import EmployeeProfile


@login_required(login_url='/authentication/login/')
@permission_required('employee.add_employeeprofile', raise_exception=True)
def create_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employee/page/create_employee.html', {'form': form})


@login_required(login_url='/authentication/login/')
def employee_list(request):
    employees = EmployeeProfile.objects.select_related('user').all()
    return render(request, 'employee/page/employee_list_page.html', {'employees': employees})
