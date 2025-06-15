from django import forms
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Button
from .models import EmployeeProfile, EmployeeAssignment


class EmployeeForm(forms.ModelForm):
    # Add User model fields
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = EmployeeProfile
        fields = ['role', 'phone']

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # If editing existing employee, populate User fields
        if self.instance and self.instance.user_id:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].initial = self.instance.user.username
            # Don't require password fields when editing
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('username', css_class='form-group mb-3'),
                    Div('email', css_class='form-group mb-3'),
                    Div('first_name', css_class='form-group mb-3'),
                    Div('last_name', css_class='form-group mb-3'),
                    css_class='col-md-6'
                ),
                Div(
                    Div('password', css_class='form-group mb-3'),
                    Div('confirm_password', css_class='form-group mb-3'),
                    Div('role', css_class='form-group mb-3'),
                    Div('phone', css_class='form-group mb-3'),
                    css_class='col-md-6'
                ),
                css_class='row'
            ),
            Div(
                Div('address', css_class='form-group'),
                css_class='col-12'
            ),
            Div(
                Div(
                    Button('cancel', 'Cancel', css_class='btn btn-secondary', onclick="window.history.back()"),
                    Submit('submit', 'Save Employee', css_class='btn btn-primary'),
                    css_class='d-flex justify-content-end gap-2 mt-4'
                ),
                css_class='row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if not self.instance.pk:  # Only validate on new employee creation
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        # Handle User model
        if self.user_instance:
            user = self.user_instance
        else:
            user = User(username=self.cleaned_data['username'])
            if self.cleaned_data.get('password'):
                user.set_password(self.cleaned_data['password'])

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        # Handle EmployeeProfile model
        employee = super().save(commit=False)
        employee.user = user

        if commit:
            employee.save()

        return employee


class EmployeeAssignmentForm(forms.ModelForm):
    class Meta:
        model = EmployeeAssignment
        fields = ['employee', 'location', 'date', 'note', 'assigned_by']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

