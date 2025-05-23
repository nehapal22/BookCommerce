from django import forms
from .models import ShippingAddress, Payment

class ShippingForm(forms.ModelForm):
    shipping_full_name = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Full Name'}), required=True)
    shipping_email = forms.EmailField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Email'}), required=True)
    shipping_address1 = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Address1'}), required=True)
    shipping_address2 = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Address2'}), required=False)
    shipping_city = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'City'}), required=True)
    shipping_state = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'State'}), required=False)
    shipping_zip_code = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'ZipCode'}), required=False)
    shipping_country = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Country'}), required=True)
    
    class Meta:
        model = ShippingAddress
        fields = ['shipping_full_name', 'shipping_email', 'shipping_address1', 'shipping_address2', 'shipping_city', 'shipping_state', 'shipping_zip_code', 'shipping_country']
        
        exclude = ['user']
        
    def __str__(self):
        return f"{self.shipping_full_name} - {self.shipping_email} - {self.shipping_address1} - {self.shipping_address2} - {self.shipping_city} - {self.shipping_state} - {self.shipping_zip_code} - {self.shipping_country}"

class paymentForm(forms.ModelForm):
    
    payment_method = forms.ChoiceField(
        label="Payment Method",
        choices=Payment.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='card'
    )
    
    card_name = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Card Name'}), required=False)
    card_number = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Card Number'}), required=False)
    card_expiry = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Card Expiry'}), required=False)
    card_cvv = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Card CVV'}), required=False)
    billing_address1 = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Billing Address1'}), required=True)
    billing_address2 = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Billing Address2'}), required=False)
    billing_city = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Billing City'}), required=True)
    billing_state = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Billing State'}), required=False)
    billing_zip_code = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Billing Zip Code'}), required=False)
    billing_country = forms.CharField(label="", max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Billing Country'}), required=True)
    
    class Meta:
        model = Payment
        fields = ['payment_method', 'card_name', 'card_number', 'card_expiry', 'card_cvv']

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        
        if payment_method == 'card':
            card_name = cleaned_data.get('card_name')
            card_number = cleaned_data.get('card_number')
            card_expiry = cleaned_data.get('card_expiry')
            card_cvv = cleaned_data.get('card_cvv')
            
            if not all([card_name, card_number, card_expiry, card_cvv]):
                raise forms.ValidationError("All card details are required for card payment")
        # For COD, we don't need to validate card details
        return cleaned_data