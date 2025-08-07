from django import forms
from .models import Healthcenters

class CenterRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = Healthcenters
        fields = ['center_name', 'center_id', 'phone', 'email', 'thaluk', 'district', 'username', 'password', 'profile_image']


class CenterLoginForm(forms.Form):
    username = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    