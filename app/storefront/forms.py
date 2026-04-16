from django import forms

from app.storefront.models import StorefrontProductReview


class StorefrontProductReviewForm(forms.ModelForm):
    class Meta:
        model = StorefrontProductReview
        fields = ['reviewer_name', 'rating', 'body']

    def clean_body(self):
        body = self.cleaned_data['body'].strip()
        if len(body) < 10:
            raise forms.ValidationError('Please provide a little more detail (minimum 10 characters).')
        return body


class StorefrontCustomerSignupForm(forms.Form):
    name = forms.CharField(max_length=255, label="Your name")
    phone_number = forms.CharField(max_length=15, label="Phone number")
    device = forms.CharField(max_length=120, label="Device you use")

    def clean_phone_number(self):
        raw = (self.cleaned_data.get("phone_number") or "").strip()
        digits = "".join(ch for ch in raw if ch.isdigit())
        if len(digits) < 7:
            raise forms.ValidationError("Please enter a valid phone number.")
        return digits

    def to_customer_kwargs(self):
        return {
            "name": self.cleaned_data["name"].strip(),
            "contact": self.cleaned_data["phone_number"],
            "device": self.cleaned_data["device"].strip(),
        }
