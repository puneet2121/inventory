from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Row, Column, Layout, Field

from .models import Profile


class EmployeeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)

        # Initialize Crispy Forms helper
        self.helper = FormHelper(self)
        self.helper.form_method = 'post'

        # Define form layout
        self.helper.layout = Layout(
            Row(
                Column('user', css_class='col-md-6'),  # User field (relation to User model)
                Column('role', css_class='col-md-6'),  # Role field
                css_class='row'
            ),
            Row(
                Column('staff_type', css_class='col-md-6'),  # Dropdown for staff type
                Column('bio', css_class='col-md-6'),  # Bio field
                css_class='row'
            ),
        )

        # Add submit button
        self.helper.add_input(Submit("submit", "Submit", css_class="btn-primary btn-sm bg-primary"))

    class Meta:
        model = Profile
        fields = ['user', 'role', 'staff_type', 'bio']  # Fields included in the form
