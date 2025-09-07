from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from .forms import EmployeeForm, EmployeeAssignmentForm
from .models import EmployeeProfile, EmployeeAssignment


@login_required(login_url='/authentication/login/')
@permission_required('employee.add_employeeprofile', raise_exception=True)
def create_or_edit_employee(request, pk=None):
    is_add = True
    if pk:
        employee = get_object_or_404(EmployeeProfile, pk=pk)  # Get existing employee for editing
        is_add = False
    else:
        employee = None  # Create a new employee if pk is not provided

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)  # Use instance for editing
        if form.is_valid():
            form.save()
            return redirect('employee:employee_list')  # Redirect after saving
    else:
        form = EmployeeForm(instance=employee)  # Pre-fill form for editing

    return render(request, 'employee/page/create_employee.html', {'form': form, 'is_add': is_add})


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

@login_required(login_url='/authentication/login/')
def assignment_create(request):
    selected_date = request.GET.get('date')
    if request.method == 'POST':
        form = EmployeeAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            assignment.save()
            return redirect('employee:assignment-calendar')
    else:
        form = EmployeeAssignmentForm(initial={'date': selected_date})
    return render(request, 'employee/page/assignment_form.html', {'form': form})


@login_required(login_url='/authentication/login/')
def assignment_calendar(request):
    return render(request, 'employee/page/assignment_calendar.html')


@login_required(login_url='/authentication/login/')
def assignment_events(request):
    assignments = EmployeeAssignment.objects.select_related('employee')
    events = []
    for a in assignments:
        events.append({
            'title': f"{a.employee.user.get_full_name()} → {a.location}",
            'start': str(a.date),
        })
    return JsonResponse(events, safe=False)
