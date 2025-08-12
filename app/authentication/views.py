from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.models import User

from app.authentication.forms import SignupForm
from app.core.models import Company
from app.employee.models import EmployeeProfile


# Create your views here.
def login_view(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            return redirect('inventory:add_product')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'authentication/login_page.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('authentication:login')


def signup_view(request):
    """
    Signup to create the first Company and an initial admin user.
    This sets the tenant_id via the created EmployeeProfile to the new company's id.
    """
    # Public signup enabled: allow creating a new company anytime.

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            company_name = form.cleaned_data['company_name']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']

            # Create company
            company = Company.objects.create(name=company_name)

            # Create user
            user = User.objects.create_user(username=username, password=password, is_superuser=True)

            # Create employee profile with admin role and set tenant_id to company.id
            profile = EmployeeProfile(user=user, role='admin')
            profile.tenant_id = company.id
            profile.save()

            # Log the user in and redirect
            login(request, user)
            messages.success(request, f"Welcome to {company.name}! Your account has been created.")
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignupForm()

    return render(request, 'authentication/signup.html', {'form': form})
