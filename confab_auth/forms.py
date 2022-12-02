from django import forms


class SignInForm(forms.Form):
    email = forms.CharField(label='Email', widget=forms.TextInput({"placeholder": "Email"}), max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput({"placeholder": "Password"}), max_length=100)

class SignUpForm(forms.Form):

    email = forms.CharField(label='Email', widget=forms.TextInput({"placeholder": "Email"}), max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput({"placeholder": "Password"}), max_length=100)
    re_password = forms.CharField(label='Password', widget=forms.PasswordInput({"placeholder": "Password"}), max_length=100)
