from django import forms
from django.contrib.auth.models import User
from .models import EmployeeProfile


class EmployeeForm(forms.ModelForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    role = forms.ChoiceField(
        choices=EmployeeProfile.ROLE_CHOICES,
        label="Role",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = EmployeeProfile
        fields = ['phone', 'address', 'role']

    def save(self, commit=True):
        # Create User
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
        )
        employee_profile = super().save(commit=False)
        employee_profile.user = user
        if commit:
            user.save()
            employee_profile.save()
        return employee_profile
